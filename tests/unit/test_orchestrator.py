from __future__ import annotations

import json
import gzip
from types import SimpleNamespace

import httpx
import pytest

from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.audit.logger import AuditLogger
from comptext_phone_agent.config import OrchestratorConfig
from comptext_phone_agent.orchestrator.catalog import TRUSTED_ACTIONS, ActionCatalog, ActionDefinition
from comptext_phone_agent.orchestrator.models import RouteDecision, RouteKind
from comptext_phone_agent.orchestrator.parser import MAX_ROUTER_RESPONSE_BYTES, parse_router_output
from comptext_phone_agent.orchestrator.router import (
    AutoRouter,
    KeywordRouter,
    LoopbackRouterClient,
    RouterError,
)
from comptext_phone_agent.orchestrator.service import OrchestratorService
from comptext_phone_agent.runtime.policy import RuntimePolicy, ToolPolicy


DECISION = {
    "kind": "direct_action",
    "action": "scan_storage",
    "arguments": {"top": 10},
    "confidence": 0.91,
    "reason": "storage request",
    "source": "broker",
}


@pytest.mark.parametrize(
    "rendered",
    [
        json.dumps(DECISION),
        f"```json\n{json.dumps(DECISION)}\n```",
        f"Broker result follows:\n{json.dumps(DECISION)}\nEnd of result.",
    ],
)
def test_route_parser_extracts_one_plain_fenced_or_surrounded_object(rendered):
    decision = parse_router_output(rendered)
    assert decision.kind is RouteKind.DIRECT_ACTION
    assert decision.action == "scan_storage"


def test_route_parser_rejects_conflicting_multiple_objects():
    rendered = f"{json.dumps(DECISION)}\n{json.dumps({**DECISION, 'action': 'device_wifi'})}"
    with pytest.raises(ValueError, match="multiple"):
        parse_router_output(rendered)


@pytest.mark.parametrize("confidence", [float("nan"), float("inf"), -0.1, 1.1])
def test_route_parser_rejects_non_finite_or_out_of_range_confidence(confidence):
    with pytest.raises(ValueError, match="confidence"):
        parse_router_output(json.dumps({**DECISION, "confidence": confidence}))


@pytest.mark.parametrize(
    "action",
    [" scan_storage", "scan_storage ", "scan storage", "ѕcan_storage", "SCAN_STORAGE"],
)
def test_route_parser_rejects_whitespace_tricked_or_confusable_actions(action):
    with pytest.raises(ValueError, match="action"):
        parse_router_output(json.dumps({**DECISION, "action": action}))


def test_route_parser_enforces_response_size_limit():
    with pytest.raises(ValueError, match="too large"):
        parse_router_output("x" * (MAX_ROUTER_RESPONSE_BYTES + 1))


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:8080",
        "http://example.com:8080",
        "http://user:pass@127.0.0.1:8080",
        "http://127.0.0.1:8080?token=secret",
        "http://127.0.0.1:8080/#fragment",
    ],
)
def test_broker_url_is_strict_loopback_http(url):
    with pytest.raises(ValueError, match="loopback"):
        LoopbackRouterClient(url, token="token")


def test_broker_requires_explicit_authentication_token():
    with pytest.raises(RouterError) as raised:
        LoopbackRouterClient("http://127.0.0.1:8080", token="")
    assert raised.value.category == "configuration"


def test_broker_rejects_redirect_without_following_it():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(302, headers={"Location": "https://attacker.test/steal"}, request=request)

    router = LoopbackRouterClient(
        "http://127.0.0.1:8080",
        token="secret",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(RouterError) as raised:
        router.route("scan storage")
    assert raised.value.category == "redirect"
    assert len(requests) == 1


def test_broker_sends_auth_to_fixed_route_endpoint_and_parses_decision():
    def handler(request):
        assert request.url.path == "/v1/route"
        assert request.headers["Authorization"] == "Bearer secret"
        assert request.headers["Accept-Encoding"] == "identity"
        return httpx.Response(200, json={"decision": DECISION}, request=request)

    router = LoopbackRouterClient(
        "http://127.0.0.1:8080",
        token="secret",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    decision = router.route("scan storage")
    assert decision.action == "scan_storage"
    assert decision.source == "broker"


@pytest.mark.parametrize(
    ("status_code", "category"),
    [(401, "authentication"), (403, "authorization"), (429, "rate_limited")],
)
def test_broker_classifies_http_errors(status_code, category):
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status_code, request=request)
        )
    )
    router = LoopbackRouterClient(
        "http://127.0.0.1:8080", token="secret", client=client
    )
    with pytest.raises(RouterError) as raised:
        router.route("scan storage")
    assert raised.value.category == category


def test_broker_limits_streamed_response_body():
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=b"x" * (MAX_ROUTER_RESPONSE_BYTES + 1),
                request=request,
            )
        )
    )
    router = LoopbackRouterClient(
        "http://127.0.0.1:8080", token="secret", client=client
    )
    with pytest.raises(RouterError) as raised:
        router.route("scan storage")
    assert raised.value.category == "response_too_large"


def test_broker_rejects_compressed_response_without_decoding_it():
    compressed = gzip.compress(b"x" * (MAX_ROUTER_RESPONSE_BYTES * 128))
    assert len(compressed) < MAX_ROUTER_RESPONSE_BYTES
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=compressed,
                headers={"Content-Encoding": "gzip"},
                request=request,
            )
        )
    )
    router = LoopbackRouterClient(
        "http://127.0.0.1:8080", token="secret", client=client
    )
    with pytest.raises(RouterError) as raised:
        router.route("scan storage")
    assert raised.value.category == "invalid_response"


def test_broker_classifies_timeout():
    def handler(request):
        raise httpx.ReadTimeout("slow broker", request=request)

    router = LoopbackRouterClient(
        "http://127.0.0.1:8080",
        token="secret",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(RouterError) as raised:
        router.route("scan storage")
    assert raised.value.category == "timeout"


def test_auto_router_falls_back_only_to_local_keyword_router():
    class OfflineBroker:
        def route(self, text):
            raise RouterError("offline", category="network")

    decision = AutoRouter(OfflineBroker(), KeywordRouter()).route("Zeige meinen Akku")
    assert decision.action == "device_battery"
    assert decision.source == "keyword_fallback"


@pytest.mark.parametrize(
    "category",
    [
        "authentication",
        "authorization",
        "invalid_response",
        "request_too_large",
        "redirect",
        "rate_limited",
        "http_error",
    ],
)
def test_auto_router_does_not_fallback_for_non_availability_errors(category):
    class BrokerFailure:
        def route(self, text):
            raise RouterError("broker rejected request", category=category)

    with pytest.raises(RouterError) as raised:
        AutoRouter(BrokerFailure(), KeywordRouter()).route("Zeige meinen Akku")
    assert raised.value.category == category


def test_auto_router_does_not_bypass_input_limit():
    class BoundedBroker:
        def route(self, text):
            if len(text.encode("utf-8")) > 16 * 1024:
                raise RouterError("router input is too large", category="request_too_large")
            raise AssertionError("test input should exceed the bound")

    oversized = "x" * (16 * 1024) + " akku"
    with pytest.raises(RouterError) as raised:
        AutoRouter(BoundedBroker(), KeywordRouter()).route(oversized)
    assert raised.value.category == "request_too_large"


def test_auto_router_allows_explicit_service_unavailable_fallback():
    class UnavailableBroker:
        def route(self, text):
            raise RouterError("broker unavailable", category="service_unavailable")

    decision = AutoRouter(UnavailableBroker(), KeywordRouter()).route("Zeige meinen Akku")
    assert decision.action == "device_battery"
    assert decision.source == "keyword_fallback"


def test_auto_router_preserves_a_successful_delegate_decision():
    class Broker:
        def route(self, text):
            return RouteDecision(
                RouteKind.DELEGATE,
                confidence=0.7,
                reason="needs planner",
                source="broker",
            )

    decision = AutoRouter(Broker(), KeywordRouter()).route("Zeige meinen Akku")
    assert decision.kind is RouteKind.DELEGATE
    assert decision.source == "broker"


def test_keyword_router_normalizes_unicode_and_whitespace():
    decision = KeywordRouter().route("  GROESSTE\t\n DATEI  ")
    assert decision.action == "largest_files"


def test_action_catalog_is_pinned_to_exact_trusted_actions():
    class Registry:
        _tools = {
            name: SimpleNamespace(
                description="test",
                parameters={"type": "object"},
                risk=0,
                read_only=True,
                approval="never",
            )
            for name in (*TRUSTED_ACTIONS, "arbitrary_shell")
        }

    catalog = ActionCatalog.from_registry(Registry())
    assert set(catalog.names()) == set(TRUSTED_ACTIONS)
    assert catalog.get("arbitrary_shell") is None


def test_orchestrator_config_supports_auto_but_rejects_unsafe_urls():
    assert OrchestratorConfig(router_mode="auto").router_mode == "auto"
    with pytest.raises(ValueError, match="loopback"):
        OrchestratorConfig(router_base_url="http://user@127.0.0.1:8080")


class _StaticRouter:
    def __init__(self, decision):
        self.decision = decision

    def route(self, text):
        return self.decision


class _Registry:
    def __init__(self):
        self.executions = 0
        self.spec = SimpleNamespace(
            parameters={
                "type": "object",
                "properties": {"top": {"type": "integer", "minimum": 1, "maximum": 100}},
                "additionalProperties": False,
            },
            policy=ToolPolicy("scan_storage", read_only=True),
        )

    def get(self, name):
        return self.spec if name == "scan_storage" else None

    def execute(self, name, arguments):
        self.executions += 1
        return {"changed": False, "top": arguments.get("top")}


def _service(decision, tmp_path):
    registry = _Registry()
    catalog = ActionCatalog(
        {
            "scan_storage": ActionDefinition(
                "scan_storage", "scan", registry.spec.parameters, 0, True, "never"
            )
        }
    )
    service = OrchestratorService(
        router=_StaticRouter(decision),
        registry=registry,
        catalog=catalog,
        policy=RuntimePolicy(registry, tmp_path),
        min_confidence=0.8,
    )
    return service, registry


def test_unknown_model_action_is_rejected_before_policy_or_execution(tmp_path):
    service, registry = _service(
        RouteDecision(RouteKind.DIRECT_ACTION, "arbitrary_shell", {}, 0.99), tmp_path
    )
    result = service.handle("ignored", execute=True)
    assert result.status == "rejected"
    assert result.error == "action_not_allowed"
    assert registry.executions == 0


def test_nonavailability_router_error_is_not_delegated(tmp_path):
    class AuthenticationFailure:
        def route(self, text):
            raise RouterError("authentication failed", category="authentication")

    service, registry = _service(
        RouteDecision(RouteKind.DELEGATE, confidence=0.5, reason="unused"), tmp_path
    )
    service.router = AuthenticationFailure()
    result = service.handle("ignored", execute=True)
    assert result.status == "error"
    assert result.decision.kind is RouteKind.REJECT
    assert result.error == "authentication"
    assert registry.executions == 0


def test_argument_mutation_is_rejected_by_strict_schema(tmp_path):
    service, registry = _service(
        RouteDecision(
            RouteKind.DIRECT_ACTION,
            "scan_storage",
            {"top": 10, "authorization": "Bearer secret"},
            0.99,
        ),
        tmp_path,
    )
    result = service.handle("ignored", execute=True)
    assert result.status == "rejected"
    assert result.error == "invalid_arguments"
    assert registry.executions == 0


def test_preview_is_default_and_does_not_execute(tmp_path):
    service, registry = _service(
        RouteDecision(RouteKind.DIRECT_ACTION, "scan_storage", {"top": 10}, 0.99),
        tmp_path,
    )
    result = service.handle("ignored")
    assert result.status == "preview"
    assert registry.executions == 0


def test_orchestrator_audit_redacts_nested_authorization(tmp_path):
    database = Database(tmp_path / "audit.sqlite3")
    audit = AuditLogger(database)
    secret = "Bearer orchestrator-secret-value"
    event_id = audit.log(
        action="orchestrator.route",
        tool="local-orchestrator",
        parameters={"decision": {"authorization": secret}, "error": secret},
    )
    rendered = json.dumps(audit.get(event_id))
    assert "orchestrator-secret-value" not in rendered
