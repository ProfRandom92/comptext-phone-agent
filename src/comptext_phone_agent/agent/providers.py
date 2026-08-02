from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
import os
import httpx

from .provider_config import DEFAULT_BASE_URLS, DEFAULT_MODELS, canonical_provider_name
from .provider_errors import ProviderError, classify_provider_error

class AgentProvider(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...

@dataclass(slots=True)
class MockProvider:
    response: str = '{"intent":"scan","top":30}'
    def complete(self, messages: list[dict[str, str]]) -> str:
        return self.response

class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str | None, model: str, timeout: int = 30, client: httpx.Client | None = None):
        self.base_url=base_url.rstrip('/'); self.api_key=api_key; self.model=model; self.timeout=timeout; self.client=client
    def complete(self, messages: list[dict[str, str]]) -> str:
        headers={"Content-Type":"application/json"}
        if self.api_key: headers["Authorization"]=f"Bearer {self.api_key}"
        client=self.client or httpx.Client(timeout=self.timeout)
        close=self.client is None
        try:
            response=client.post(f"{self.base_url}/chat/completions",headers=headers,json={"model":self.model,"messages":messages,"temperature":0})
            response.raise_for_status(); data=response.json()
            return str(data["choices"][0]["message"]["content"])
        except httpx.HTTPError as error:
            raise classify_provider_error(error, label="provider") from error
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise ProviderError("provider returned an invalid response", category="invalid_response") from error
        finally:
            if close: client.close()

class GeminiProvider:
    def __init__(self, api_key: str, model: str|None=None, timeout: int=30, client: httpx.Client | None=None):
        self.api_key=api_key; self.model=model or DEFAULT_MODELS["gemini"]; self.timeout=timeout; self.client=client
    def complete(self, messages: list[dict[str, str]]) -> str:
        prompt="\n".join(f"{x['role']}: {x['content']}" for x in messages)
        client=self.client or httpx.Client(timeout=self.timeout); close=self.client is None
        try:
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            response=client.post(url,headers={"x-goog-api-key":self.api_key},json={"contents":[{"parts":[{"text":prompt}]}]})
            response.raise_for_status(); data=response.json()
            return str(data["candidates"][0]["content"]["parts"][0]["text"])
        except httpx.HTTPError as error:
            raise classify_provider_error(error, label="Gemini") from error
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise ProviderError("Gemini returned an invalid response", category="invalid_response") from error
        finally:
            if close: client.close()

def create_provider(name: str, model: str | None=None, base_url: str | None=None, timeout: int=30) -> AgentProvider:
    try:
        key=canonical_provider_name(name)
    except ValueError as error:
        raise ProviderError(str(error), category="configuration") from error
    if key == "mock": return MockProvider()
    if key == "openai":
        token=os.environ.get("OPENAI_API_KEY")
        if not token: raise ProviderError("OPENAI_API_KEY is not set", category="configuration")
        return OpenAICompatibleProvider(base_url or DEFAULT_BASE_URLS[key],token,model or DEFAULT_MODELS[key],timeout)
    if key == "openrouter":
        token=os.environ.get("OPENROUTER_API_KEY")
        if not token: raise ProviderError("OPENROUTER_API_KEY is not set", category="configuration")
        return OpenAICompatibleProvider(base_url or DEFAULT_BASE_URLS[key],token,model or DEFAULT_MODELS[key],timeout)
    if key == "nvidia":
        token=os.environ.get("NVIDIA_API_KEY")
        if not token: raise ProviderError("NVIDIA_API_KEY is not set", category="configuration")
        return OpenAICompatibleProvider(base_url or DEFAULT_BASE_URLS[key],token,model or DEFAULT_MODELS[key],timeout)
    if key == "gemini":
        token=os.environ.get("GEMINI_API_KEY")
        if not token: raise ProviderError("GEMINI_API_KEY is not set", category="configuration")
        return GeminiProvider(token,model or DEFAULT_MODELS[key],timeout)
    if key == "local":
        return OpenAICompatibleProvider(base_url or os.environ.get("LOCAL_OPENAI_BASE_URL",DEFAULT_BASE_URLS[key]),None,model or DEFAULT_MODELS[key],timeout)
    if key == "ollama-cloud":
        token=os.environ.get("OLLAMA_API_KEY")
        if not token: raise ProviderError("OLLAMA_API_KEY is not set", category="configuration")
        return OpenAICompatibleProvider(base_url or DEFAULT_BASE_URLS[key],token,model or DEFAULT_MODELS[key],timeout)
    raise ProviderError(f"unsupported provider: {name}", category="configuration")
