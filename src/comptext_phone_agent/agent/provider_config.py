from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from ..config import AgentConfig


FALLBACK_PROVIDER = "ollama-cloud"
DEFAULT_MODELS = MappingProxyType(
    {
        "gemini": "gemini-2.5-flash",
        "local": "local-model",
        "mock": "mock-model",
        "nvidia": "meta/llama-3.1-8b-instruct",
        "ollama-cloud": "gpt-oss:20b",
        "openai": "gpt-4.1-mini",
        "openrouter": "openai/gpt-4.1-mini",
    }
)
DEFAULT_BASE_URLS = MappingProxyType(
    {
        "gemini": "https://generativelanguage.googleapis.com/v1beta",
        "local": "http://127.0.0.1:11434/v1",
        "mock": "",
        "nvidia": "https://integrate.api.nvidia.com/v1",
        "ollama-cloud": "https://ollama.com",
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
    }
)
PROVIDER_ALIASES = MappingProxyType(
    {
        "gemini": "gemini",
        "local": "local",
        "mock": "mock",
        "nim": "nvidia",
        "nvidia": "nvidia",
        "nvidia-nim": "nvidia",
        "ollama": "ollama-cloud",
        "ollama-cloud": "ollama-cloud",
        "openai": "openai",
        "openrouter": "openrouter",
    }
)
CREDENTIAL_ENV = MappingProxyType(
    {
        "gemini": "GEMINI_API_KEY",
        "nvidia": "NVIDIA_API_KEY",
        "ollama-cloud": "OLLAMA_API_KEY",
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
)


class ProviderConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EffectiveProviderConfig:
    provider: str
    model: str
    base_url: str
    timeout_seconds: int
    sources: Mapping[str, str]
    credential_configured: bool

    def diagnostics(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "timeout_seconds": self.timeout_seconds,
            "sources": dict(self.sources),
            "credential_configured": self.credential_configured,
        }


def canonical_provider_name(value: str) -> str:
    key = value.strip().casefold().replace("_", "-")
    try:
        return PROVIDER_ALIASES[key]
    except KeyError as error:
        raise ProviderConfigError(f"unknown provider: {value}") from error


def _first_value(*candidates: tuple[str | None, str]) -> tuple[str, str]:
    for value, source in candidates:
        if value is not None and str(value).strip():
            return str(value).strip(), source
    raise ProviderConfigError("provider configuration has no usable value")


def resolve_provider_config(
    config: AgentConfig,
    *,
    cli_provider: str | None = None,
    cli_model: str | None = None,
    cli_base_url: str | None = None,
    cli_timeout_seconds: int | None = None,
    environment: Mapping[str, str] | None = None,
) -> EffectiveProviderConfig:
    if environment is None:
        import os

        environment = os.environ

    provider_value, provider_source = _first_value(
        (cli_provider, "cli"),
        (config.provider, "config"),
        (environment.get("COMPTEXT_AGENT_PROVIDER"), "environment"),
        (FALLBACK_PROVIDER, "fallback"),
    )
    provider = canonical_provider_name(provider_value)

    legacy_model = environment.get("OLLAMA_MODEL") if provider == "ollama-cloud" else None
    model, model_source = _first_value(
        (cli_model, "cli"),
        (config.model, "config"),
        (environment.get("COMPTEXT_AGENT_MODEL"), "environment"),
        (legacy_model, "environment"),
        (DEFAULT_MODELS[provider], "fallback"),
    )

    provider_base_environment = None
    if provider == "ollama-cloud":
        provider_base_environment = environment.get("OLLAMA_HOST")
    elif provider == "local":
        provider_base_environment = environment.get("LOCAL_OPENAI_BASE_URL")
    base_candidates = (
        (cli_base_url, "cli"),
        (config.base_url, "config"),
        (environment.get("COMPTEXT_AGENT_BASE_URL"), "environment"),
        (provider_base_environment, "environment"),
    )
    for candidate, candidate_source in base_candidates:
        if candidate is not None and str(candidate).strip():
            base_url, base_url_source = str(candidate).strip(), candidate_source
            break
    else:
        base_url, base_url_source = DEFAULT_BASE_URLS[provider], "fallback"

    if cli_timeout_seconds is not None:
        timeout_seconds = cli_timeout_seconds
        timeout_source = "cli"
    elif environment.get("COMPTEXT_AGENT_TIMEOUT_SECONDS") and config.timeout_seconds == 30:
        try:
            timeout_seconds = int(environment["COMPTEXT_AGENT_TIMEOUT_SECONDS"])
        except ValueError as error:
            raise ProviderConfigError("COMPTEXT_AGENT_TIMEOUT_SECONDS must be an integer") from error
        timeout_source = "environment"
    else:
        timeout_seconds = config.timeout_seconds
        timeout_source = "config"
    if timeout_seconds <= 0:
        raise ProviderConfigError("timeout_seconds must be positive")

    credential_name = CREDENTIAL_ENV.get(provider)
    credential_configured = bool(credential_name and environment.get(credential_name))
    return EffectiveProviderConfig(
        provider=provider,
        model=model,
        base_url=base_url.rstrip("/"),
        timeout_seconds=timeout_seconds,
        sources=MappingProxyType(
            {
                "provider": provider_source,
                "model": model_source,
                "base_url": base_url_source,
                "timeout_seconds": timeout_source,
            }
        ),
        credential_configured=credential_configured,
    )
