from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ToolProposal:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ModelTurn:
    content: str = ""
    tool_calls: list[ToolProposal] = field(default_factory=list)


class RuntimeModel(Protocol):
    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelTurn: ...
