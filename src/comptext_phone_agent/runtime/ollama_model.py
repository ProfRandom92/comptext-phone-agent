from __future__ import annotations
import uuid
from .model import ModelTurn, ToolProposal
from ..agent.ollama_client import extract_tool_calls


class OllamaRuntimeModel:
    def __init__(self, client): self.client=client
    def complete(self,messages,tools):
        response=self.client.chat(messages,tools,stream=False)
        message=response.message if hasattr(response,'message') else response.get('message',{})
        content=getattr(message,'content','') if not isinstance(message,dict) else message.get('content','')
        calls=[]
        for call in extract_tool_calls(message):
            calls.append(ToolProposal(str(uuid.uuid4()),call.name,call.arguments))
        return ModelTurn(str(content or ''),calls)
