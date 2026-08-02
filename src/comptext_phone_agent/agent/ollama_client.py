from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterator
import os
import httpx

class OllamaChatError(RuntimeError): pass

@dataclass(slots=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]

@dataclass(slots=True)
class ChatMessage:
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None

@dataclass(slots=True)
class ChatResponse:
    message: ChatMessage

class OllamaCloudClient:
    """Termux-safe Ollama Cloud client implementing the native /api/chat schema."""
    def __init__(self, model: str|None=None, api_key: str|None=None, host: str="https://ollama.com", timeout: int=180, client: httpx.Client|None=None):
        self.model=model or os.environ.get("OLLAMA_MODEL","gpt-oss:20b")
        self.api_key=api_key or os.environ.get("OLLAMA_API_KEY")
        if not self.api_key: raise OllamaChatError("OLLAMA_API_KEY is not set")
        self.host=host.rstrip('/'); self.timeout=timeout; self._client=client
    def chat(self,messages:list[dict[str,Any]],tools:list[dict[str,Any]],stream:bool=True):
        headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"}
        payload={"model":self.model,"messages":messages,"tools":tools,"stream":stream}
        client=self._client or httpx.Client(timeout=self.timeout); close=self._client is None
        try:
            if stream:
                def iterator() -> Iterator[ChatResponse]:
                    try:
                        with client.stream("POST",f"{self.host}/api/chat",headers=headers,json=payload) as response:
                            response.raise_for_status()
                            for line in response.iter_lines():
                                if not line: continue
                                data=httpx.Response(200,content=line).json(); msg=data.get("message",{})
                                yield ChatResponse(ChatMessage(str(msg.get("content",'')),msg.get("tool_calls")))
                    except (httpx.HTTPError,ValueError) as exc: raise OllamaChatError(str(exc)) from exc
                    finally:
                        if close: client.close()
                return iterator()
            response=client.post(f"{self.host}/api/chat",headers=headers,json=payload)
            response.raise_for_status(); data=response.json(); msg=data.get("message",{})
            return ChatResponse(ChatMessage(str(msg.get("content",'')),msg.get("tool_calls")))
        except (httpx.HTTPError,ValueError) as exc:
            if close: client.close()
            raise OllamaChatError(str(exc)) from exc

def extract_tool_calls(message: Any) -> list[ToolCall]:
    raw=getattr(message,"tool_calls",None) if not isinstance(message,dict) else message.get("tool_calls")
    result=[]
    for item in raw or []:
        fn=getattr(item,"function",None) if not isinstance(item,dict) else item.get("function",{})
        name=getattr(fn,"name",None) if not isinstance(fn,dict) else fn.get("name")
        args=getattr(fn,"arguments",None) if not isinstance(fn,dict) else fn.get("arguments",{})
        if name: result.append(ToolCall(str(name),dict(args or {})))
    return result
