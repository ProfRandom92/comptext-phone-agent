from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import IntEnum, StrEnum
from typing import Any
import hashlib, json, uuid

class OperatingMode(StrEnum):
    ANALYSIS = "analysis"
    ORGANIZE = "organize"
    CONTROLLED = "controlled"

class RiskClass(IntEnum):
    READ_ONLY = 0
    REVERSIBLE = 1
    EXTERNAL_OR_BATCH = 2
    IRREVERSIBLE = 3

@dataclass(slots=True)
class FileRecord:
    absolute_path: str
    relative_path: str
    name: str
    extension: str
    category: str
    size: int
    mtime: float
    atime: float | None
    source: str
    sha256: str | None = None
    partial_hash: str | None = None
    exclusion_reason: str | None = None
    scan_error: str | None = None
    is_symlink: bool = False
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(slots=True)
class ScanResult:
    root: str
    started_at: str
    completed_at: str
    files: list[FileRecord] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    @property
    def total_files(self) -> int:
        return len(self.files)
    @property
    def total_size(self) -> int:
        return sum(x.size for x in self.files if not x.scan_error)
    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root, "started_at": self.started_at, "completed_at": self.completed_at,
            "total_files": self.total_files, "total_size": self.total_size,
            "files": [x.to_dict() for x in self.files], "errors": self.errors,
        }

@dataclass(slots=True)
class PlanAction:
    action: str
    source: str
    target: str | None
    size: int
    reason: str
    risk: RiskClass
    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["risk"] = int(self.risk)
        return d

@dataclass(slots=True)
class ActionPlan:
    id: str
    session_id: str
    created_at: str
    mode: OperatingMode
    actions: list[PlanAction]
    description: str
    @classmethod
    def create(cls, session_id: str, mode: OperatingMode, actions: list[PlanAction], description: str) -> "ActionPlan":
        return cls(str(uuid.uuid4()), session_id, datetime.now(timezone.utc).isoformat(), mode, actions, description)
    @property
    def total_size(self) -> int:
        return sum(a.size for a in self.actions)
    @property
    def risk(self) -> RiskClass:
        return max((a.risk for a in self.actions), default=RiskClass.READ_ONLY)
    @property
    def plan_hash(self) -> str:
        payload = {
            "id": self.id, "session_id": self.session_id, "mode": self.mode.value,
            "actions": [a.to_dict() for a in self.actions], "description": self.description,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "session_id": self.session_id, "created_at": self.created_at, "mode": self.mode.value,
            "actions": [a.to_dict() for a in self.actions], "description": self.description,
            "total_size": self.total_size, "risk": int(self.risk), "plan_hash": self.plan_hash,
        }

@dataclass(slots=True)
class ApprovalClaims:
    approval_id: str
    installation_id: str
    user_id: str
    session_id: str
    action_type: str
    sources: list[str]
    targets: list[str]
    file_count: int
    total_size: int
    plan_hash: str
    created_at: int
    expires_at: int
    risk: int
    nonce: str
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
