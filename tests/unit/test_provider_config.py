from __future__ import annotations

import importlib
import importlib.util
import json

from comptext_phone_agent.config import AgentConfig


def provider_config_module():
    spec = importlib.util.find_spec("comptext_phone_agent.agent.provider_config")
    assert spec is not None, "central provider configuration module is missing"
    return importlib.import_module("comptext_phone_agent.agent.provider_config")


def test_cli_values_override_config_and_environment():
    module = provider_config_module()
    environment = {
        "COMPTEXT_AGENT_PROVIDER": "openrouter",
        "COMPTEXT_AGENT_MODEL": "environment-model",
        "COMPTEXT_AGENT_BASE_URL": "https://environment.test/v1",
    }

    effective = module.resolve_provider_config(
        AgentConfig(
            provider="openai",
            model="config-model",
            base_url="https://config.test/v1",
            timeout_seconds=45,
        ),
        cli_provider="ollama-cloud",
        cli_model="cli-model",
        cli_base_url="https://cli.test",
        environment=environment,
    )

    assert effective.provider == "ollama-cloud"
    assert effective.model == "cli-model"
    assert effective.base_url == "https://cli.test"
    assert effective.sources == {
        "provider": "cli",
        "model": "cli",
        "base_url": "cli",
        "timeout_seconds": "config",
    }


def test_config_values_override_environment():
    module = provider_config_module()

    effective = module.resolve_provider_config(
        AgentConfig(provider="openai", model="config-model"),
        environment={
            "COMPTEXT_AGENT_PROVIDER": "openrouter",
            "COMPTEXT_AGENT_MODEL": "environment-model",
        },
    )

    assert effective.provider == "openai"
    assert effective.model == "config-model"
    assert effective.sources["provider"] == "config"
    assert effective.sources["model"] == "config"


def test_environment_values_override_documented_fallback():
    module = provider_config_module()

    effective = module.resolve_provider_config(
        AgentConfig(provider="", model="", base_url=""),
        environment={
            "COMPTEXT_AGENT_PROVIDER": "ollama-cloud",
            "OLLAMA_MODEL": "environment-model",
        },
    )

    assert effective.provider == "ollama-cloud"
    assert effective.model == "environment-model"
    assert effective.sources["provider"] == "environment"
    assert effective.sources["model"] == "environment"


def test_fallback_is_explicit_and_not_qwen_pro():
    module = provider_config_module()

    effective = module.resolve_provider_config(
        AgentConfig(provider="", model="", base_url=""),
        environment={},
    )

    assert effective.provider == "ollama-cloud"
    assert effective.model == "gpt-oss:20b"
    assert "qwen" not in effective.model.casefold()
    assert effective.sources["model"] == "fallback"


def test_diagnostics_never_include_credentials():
    module = provider_config_module()
    secret = "do-not-render-this-key"

    effective = module.resolve_provider_config(
        AgentConfig(provider="", model="", base_url=""),
        environment={"OLLAMA_API_KEY": secret},
    )
    rendered = json.dumps(effective.diagnostics())

    assert secret not in rendered
    assert effective.diagnostics()["credential_configured"] is True


def test_mock_provider_can_use_an_empty_fallback_base_url():
    module = provider_config_module()

    effective = module.resolve_provider_config(
        AgentConfig(provider="mock", model=""),
        environment={},
    )

    assert effective.provider == "mock"
    assert effective.base_url == ""


def test_keyword_router_does_not_require_cloud_credentials(monkeypatch):
    for name in (
        "GEMINI_API_KEY",
        "NVIDIA_API_KEY",
        "OLLAMA_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    from comptext_phone_agent.orchestrator.router import KeywordRouter

    decision = KeywordRouter().route("Zeige meinen Akkustand")
    assert decision.action == "device_battery"
    assert decision.source == "keyword"
