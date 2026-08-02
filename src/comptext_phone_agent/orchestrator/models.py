from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class RouteKind(str, Enum):
    DIRECT_ACTION='direct_action'
    PLANNER='planner'
    CLARIFY='clarify'
    REJECT='reject'

@dataclass(frozen=True, slots=True)
class RouteDecision:
    kind: RouteKind
    action: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reason: str = ''
    source: str = 'router'

@dataclass(frozen=True, slots=True)
class OrchestratorResult:
    decision: RouteDecision
    status: str
    result: Any = None
    approval_required: bool = False
    error: str | None = None
