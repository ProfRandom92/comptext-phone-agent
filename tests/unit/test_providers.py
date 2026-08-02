from pathlib import Path
import json, httpx, pytest
from comptext_phone_agent.agent.providers import MockProvider, OpenAICompatibleProvider, ProviderError, create_provider
from comptext_phone_agent.agent.provider_planner import ProviderBackedPlanner

def test_mock_provider():
    assert 'scan' in MockProvider().complete([])

def test_openai_compatible_provider_uses_typed_http():
    def handler(request):
        assert request.url.path.endswith('/chat/completions')
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"intent":"scan"}'}}]})
    client=httpx.Client(transport=httpx.MockTransport(handler))
    value=OpenAICompatibleProvider('https://example.test/v1','secret','model',client=client).complete([{'role':'user','content':'scan'}])
    assert json.loads(value)['intent']=='scan'

def test_provider_planner_restricts_intents(tmp_path):
    root=tmp_path/'phone'; root.mkdir()
    planner=ProviderBackedPlanner(MockProvider('{"intent":"cleanup_plan","path":"%s"}' % root))
    result=planner.interpret('delete things',root)
    assert result['plan_only'] is True

def test_provider_planner_rejects_untyped_delete(tmp_path):
    root=tmp_path/'phone'; root.mkdir()
    with pytest.raises(ProviderError):
        ProviderBackedPlanner(MockProvider('{"intent":"delete"}')).interpret('delete',root)

def test_provider_factory_requires_secret(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    with pytest.raises(ProviderError): create_provider('openai')
    assert create_provider('local')


@pytest.mark.parametrize(
    ("status_code", "category"),
    [
        (401, "authentication"),
        (403, "authorization"),
        (404, "not_found"),
        (429, "rate_limited"),
    ],
)
def test_openai_provider_classifies_http_failures(status_code, category):
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status_code, request=request)
        )
    )
    provider = OpenAICompatibleProvider(
        "https://example.test/v1",
        "secret",
        "configured-model",
        client=client,
    )

    with pytest.raises(ProviderError) as raised:
        provider.complete([{"role": "user", "content": "hello"}])

    assert raised.value.category == category
    assert raised.value.status_code == status_code
    assert provider.model == "configured-model"


@pytest.mark.parametrize(
    ("error_type", "category"),
    [
        (httpx.ReadTimeout, "timeout"),
        (httpx.ConnectError, "network"),
    ],
)
def test_openai_provider_classifies_transport_failures(error_type, category):
    def handler(request):
        raise error_type("provider unavailable", request=request)

    provider = OpenAICompatibleProvider(
        "https://example.test/v1",
        "secret",
        "configured-model",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ProviderError) as raised:
        provider.complete([{"role": "user", "content": "hello"}])

    assert raised.value.category == category
