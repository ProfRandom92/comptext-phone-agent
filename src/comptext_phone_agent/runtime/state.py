from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import threading


class RunState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    WAITING_MODEL = "waiting_model"
    VALIDATING_TOOL = "validating_tool"
    RUNNING_TOOL = "running_tool"
    OBSERVING = "observing"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_TRANSITIONS = {
    RunState.IDLE: {RunState.PLANNING},
    RunState.PLANNING: {RunState.WAITING_MODEL, RunState.CANCELLED, RunState.FAILED},
    RunState.WAITING_MODEL: {RunState.VALIDATING_TOOL, RunState.COMPLETED, RunState.CANCELLED, RunState.FAILED},
    RunState.VALIDATING_TOOL: {RunState.RUNNING_TOOL, RunState.WAITING_APPROVAL, RunState.FAILED, RunState.CANCELLED},
    RunState.RUNNING_TOOL: {RunState.OBSERVING, RunState.FAILED, RunState.CANCELLED},
    RunState.OBSERVING: {RunState.WAITING_MODEL, RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED},
    RunState.WAITING_APPROVAL: {RunState.RUNNING_TOOL, RunState.CANCELLED, RunState.FAILED},
    RunState.COMPLETED: set(), RunState.FAILED: set(), RunState.CANCELLED: set(),
}


class InvalidStateTransition(RuntimeError):
    pass


class RunStateMachine:
    def __init__(self, initial: RunState = RunState.IDLE):
        self.state = initial

    def transition(self, target: RunState) -> RunState:
        if target not in _TRANSITIONS[self.state]:
            raise InvalidStateTransition(f"invalid transition: {self.state.value} -> {target.value}")
        self.state = target
        return target


class CancellationToken:
    def __init__(self):
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise RuntimeError("run cancelled")
