from __future__ import annotations
from pathlib import Path
from ..models import ActionPlan, OperatingMode
from ..storage.cleanup import CleanupPlanner
from ..storage.scanner import StorageScanner

class AgentPlanner:
    """Deterministic, typed planner used by CLI and Mock provider."""
    def __init__(self, scanner: StorageScanner, cleanup: CleanupPlanner):
        self.scanner = scanner
        self.cleanup = cleanup
    def cleanup_plan(self, root: Path, session_id: str = "local") -> ActionPlan:
        return self.cleanup.plan(self.scanner.scan(root), session_id=session_id)
    def interpret(self, text: str, root: Path) -> dict:
        lower = text.lower()
        if any(word in lower for word in ["delete", "lösche", "remove"]):
            return {"intent": "plan_only", "message": "Destructive language is converted to a plan; no direct action is executed."}
        if "duplicate" in lower or "doppelt" in lower:
            return {"intent": "duplicates", "path": str(root)}
        return {"intent": "scan", "path": str(root)}
