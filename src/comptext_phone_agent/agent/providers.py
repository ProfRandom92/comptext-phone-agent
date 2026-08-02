from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any
import os
import httpx

class ProviderError(RuntimeError):
    pass

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
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            raise ProviderError(f"provider request failed: {error}") from error
        finally:
            if close: client.close()

class GeminiProvider:
    def __init__(self, api_key: str, model: str="gemini-2.5-flash", timeout: int=30, client: httpx.Client | None=None):
        self.api_key=api_key; self.model=model; self.timeout=timeout; self.client=client
    def complete(self, messages: list[dict[str, str]]) -> str:
        prompt="\n".join(f"{x['role']}: {x['content']}" for x in messages)
        client=self.client or httpx.Client(timeout=self.timeout); close=self.client is None
        try:
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            response=client.post(url,headers={"x-goog-api-key":self.api_key},json={"contents":[{"parts":[{"text":prompt}]}]})
            response.raise_for_status(); data=response.json()
            return str(data["candidates"][0]["content"]["parts"][0]["text"])
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            raise ProviderError(f"Gemini request failed: {error}") from error
        finally:
            if close: client.close()

def create_provider(name: str, model: str | None=None, base_url: str | None=None, timeout: int=30) -> AgentProvider:
    key=name.lower().replace('-','_')
    if key == "mock": return MockProvider()
    if key == "openai":
        token=os.environ.get("OPENAI_API_KEY")
        if not token: raise ProviderError("OPENAI_API_KEY is not set")
        return OpenAICompatibleProvider(base_url or "https://api.openai.com/v1",token,model or "gpt-4.1-mini",timeout)
    if key == "openrouter":
        token=os.environ.get("OPENROUTER_API_KEY")
        if not token: raise ProviderError("OPENROUTER_API_KEY is not set")
        return OpenAICompatibleProvider(base_url or "https://openrouter.ai/api/v1",token,model or "openai/gpt-4.1-mini",timeout)
    if key in {"nvidia","nvidia_nim","nim"}:
        token=os.environ.get("NVIDIA_API_KEY")
        if not token: raise ProviderError("NVIDIA_API_KEY is not set")
        return OpenAICompatibleProvider(base_url or "https://integrate.api.nvidia.com/v1",token,model or "meta/llama-3.1-8b-instruct",timeout)
    if key == "gemini":
        token=os.environ.get("GEMINI_API_KEY")
        if not token: raise ProviderError("GEMINI_API_KEY is not set")
        return GeminiProvider(token,model or "gemini-2.5-flash",timeout)
    if key in {"local","ollama"}:
        return OpenAICompatibleProvider(base_url or os.environ.get("LOCAL_OPENAI_BASE_URL","http://127.0.0.1:11434/v1"),None,model or "local-model",timeout)
    raise ProviderError(f"unknown provider: {name}")
