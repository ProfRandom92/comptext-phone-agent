from __future__ import annotations
from dataclasses import dataclass, field
import json
import time
from typing import Any


class LoopLimitError(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(slots=True)
class LoopBudget:
    max_model_turns: int = 6
    max_tool_calls: int = 8
    max_identical_calls: int = 2
    max_runtime_seconds: float = 300.0
    started_at: float = field(default_factory=time.monotonic)
    model_turns: int = 0
    tool_calls: int = 0
    call_counts: dict[str, int] = field(default_factory=dict)

    def check_runtime(self) -> None:
        if time.monotonic() - self.started_at > self.max_runtime_seconds:
            raise LoopLimitError("runtime_limit")

    def record_model_turn(self) -> None:
        self.check_runtime()
        self.model_turns += 1
        if self.model_turns > self.max_model_turns:
            raise LoopLimitError("model_turn_limit")

    def record_tool_call(self, name: str, arguments: dict[str, Any]) -> None:
        self.check_runtime()
        self.tool_calls += 1
        if self.tool_calls > self.max_tool_calls:
            raise LoopLimitError("tool_call_limit")
        key = name + ":" + json.dumps(arguments, sort_keys=True, separators=(",", ":"), default=str)
        self.call_counts[key] = self.call_counts.get(key, 0) + 1
        if self.call_counts[key] > self.max_identical_calls:
            raise LoopLimitError("repeated_tool_call")
