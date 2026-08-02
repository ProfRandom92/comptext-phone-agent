from __future__ import annotations
from pathlib import Path
import time
from ..models import ActionPlan, OperatingMode, PlanAction, RiskClass, ScanResult
from .exclusions import ExclusionEngine

class CleanupPlanner:
    def __init__(self, exclusions: ExclusionEngine):
        self.exclusions = exclusions
    def plan(self, result: ScanResult, session_id: str = "local", old_days: int = 365, max_files: int = 100) -> ActionPlan:
        cutoff = time.time() - old_days * 86400
        actions: list[PlanAction] = []
        for item in sorted(result.files, key=lambda x: x.size, reverse=True):
            if len(actions) >= max_files:
                break
            if item.scan_error or item.is_symlink or item.mtime >= cutoff:
                continue
            if item.category not in {"apk", "archive", "temporary", "cache"}:
                continue
            if item.exclusion_reason:
                continue
            actions.append(PlanAction("trash", item.absolute_path, None, item.size, f"old {item.category}; mtime-based age", RiskClass.REVERSIBLE))
        return ActionPlan.create(session_id, OperatingMode.ORGANIZE, actions, "Move old, unprotected APK/archive/temp/cache files to the CompText trash.")
