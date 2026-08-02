from __future__ import annotations
from pathlib import Path
from ..models import ActionPlan, OperatingMode, PlanAction, RiskClass
from ..storage.exclusions import ExclusionEngine

class BackupPlanner:
    def __init__(self, exclusions: ExclusionEngine):
        self.exclusions = exclusions
    def plan(self, files: list[Path], destination: str, session_id: str = "local") -> ActionPlan:
        actions = []
        for path in files:
            self.exclusions.assert_can_upload(path)
            if not path.is_file():
                raise FileNotFoundError(path)
            actions.append(PlanAction("upload", str(path.resolve()), destination, path.stat().st_size, "explicit backup selection", RiskClass.EXTERNAL_OR_BATCH))
        return ActionPlan.create(session_id, OperatingMode.CONTROLLED, actions, f"Upload {len(actions)} files to {destination} without local deletion.")
