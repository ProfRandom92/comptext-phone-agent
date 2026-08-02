from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class LayoutMode(str, Enum):
    COMPACT = "compact"
    WIDE = "wide"
    DESKTOP = "desktop"

def layout_mode(width: int) -> LayoutMode:
    if width < 60:
        return LayoutMode.COMPACT
    if width < 90:
        return LayoutMode.WIDE
    return LayoutMode.DESKTOP

@dataclass(frozen=True, slots=True)
class StatusView:
    model: str = "unknown"
    mode: str = "ANALYZE"
    safe_mode: bool = False
    cloud_connected: bool = True
    battery_percent: int | None = None
    free_storage: str | None = None
    protections: tuple[str, ...] = ("Privacy Guard", "Data Shield", "Network Guard")

@dataclass(frozen=True, slots=True)
class ToolCardView:
    kind: str
    title: str
    state: str
    summary: str
    details: tuple[tuple[str, str], ...] = ()
    progress: int | None = None
    changed: bool = False
    protected: bool = False
    approval_id: str | None = None
    call_id: str = ""

@dataclass(frozen=True, slots=True)
class TranscriptItem:
    kind: str
    title: str
    body: str
    timestamp: str = ""
    tool: ToolCardView | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class AppViewState:
    session_id: str = ""
    run_id: str = ""
    status: StatusView = field(default_factory=StatusView)
    items: tuple[TranscriptItem, ...] = ()
    running: bool = False
    stop_reason: str | None = None
