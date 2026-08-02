from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any

class SignalType(str, Enum):
    CANCEL='cancel'
    APPROVE='approve'
    REJECT='reject'
    RESUME='resume'

@dataclass(frozen=True, slots=True)
class RunSignal:
    id: int
    run_id: str
    signal_type: SignalType
    payload: dict[str, Any]
    created_at: str
    consumed_at: str | None = None
