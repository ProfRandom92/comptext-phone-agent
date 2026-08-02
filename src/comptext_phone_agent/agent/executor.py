from __future__ import annotations
from pathlib import Path
from ..approvals.engine import ApprovalEngine
from ..approvals.policy import require_mode
from ..audit.logger import AuditLogger
from ..models import ActionPlan
from ..storage.trash import TrashManager

class PlanExecutor:
    def __init__(self, approvals: ApprovalEngine, trash: TrashManager, audit: AuditLogger):
        self.approvals = approvals
        self.trash = trash
        self.audit = audit
    def apply(self, plan: ActionPlan, token: str, allowed_root: Path) -> list[str]:
        require_mode(plan.mode, plan.risk)
        claims = self.approvals.verify(token, plan, consume=False)
        # Validate every action before consuming the token.
        for action in plan.actions:
            if action.action != "trash":
                raise PermissionError(f"unsupported action: {action.action}")
            self.trash.exclusions.assert_can_modify(action.source, allowed_root)
            path = Path(action.source).resolve()
            if not (path == allowed_root.resolve() or allowed_root.resolve() in path.parents):
                raise PermissionError("action outside approved storage root")
        claims = self.approvals.verify(token, plan, consume=True)
        ids = [self.trash.move(Path(action.source), claims.approval_id, allowed_root) for action in plan.actions]
        self.audit.log(action="plan.applied", tool="executor", paths=[x.source for x in plan.actions], plan_id=plan.id, approval_id=claims.approval_id, file_count=len(ids), byte_count=plan.total_size)
        return ids
