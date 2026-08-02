from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import math
import re
from typing import Any

_ACTION_NAME = re.compile(r"[a-z][a-z0-9_]*\Z", re.ASCII)
_SOURCE_NAME = re.compile(r"[a-z][a-z0-9_-]*\Z", re.ASCII)

class RouteKind(str, Enum):
    DIRECT_ACTION='direct_action'
    DELEGATE='delegate'
    PLANNER='delegate'  # Backward-compatible Python alias; serialized form is canonical.
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

    def __post_init__(self) -> None:
        if not isinstance(self.arguments, dict):
            raise ValueError('arguments must be an object')
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise ValueError('confidence must be a number')
        if not math.isfinite(float(self.confidence)) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError('confidence must be finite and between 0 and 1')
        if not isinstance(self.reason, str) or len(self.reason) > 1024:
            raise ValueError('reason must be a bounded string')
        if not isinstance(self.source, str) or not _SOURCE_NAME.fullmatch(self.source):
            raise ValueError('source must be a canonical identifier')
        if self.kind is RouteKind.DIRECT_ACTION:
            if not isinstance(self.action, str) or not _ACTION_NAME.fullmatch(self.action):
                raise ValueError('direct action requires a canonical action name')
        elif self.action is not None:
            raise ValueError('non-action routes cannot contain an action')

@dataclass(frozen=True, slots=True)
class OrchestratorResult:
    decision: RouteDecision
    status: str
    result: Any = None
    approval_required: bool = False
    error: str | None = None
