from pathlib import Path
import pytest
from comptext_phone_agent.agent.executor import PlanExecutor
from comptext_phone_agent.approvals.engine import ApprovalEngine
from comptext_phone_agent.approvals.policy import PolicyError
from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.audit.logger import AuditLogger
from comptext_phone_agent.config import load_config
from comptext_phone_agent.models import ActionPlan, OperatingMode, PlanAction, RiskClass
from comptext_phone_agent.storage.exclusions import ExclusionEngine
from comptext_phone_agent.storage.trash import TrashManager

def services(tmp_path, phone):
    db = Database(tmp_path / "state.db")
    approvals = ApprovalEngine(db, tmp_path / "data")
    exclusions = ExclusionEngine(load_config(Path("/missing")).exclusions)
    trash = TrashManager(phone / ".CompTextTrash", db, exclusions)
    return approvals, trash, AuditLogger(db)

def test_plan_without_approval_blocked(tmp_path, phone):
    approvals, trash, audit = services(tmp_path, phone)
    source = phone / "Download/old-installer.apk"
    plan = ActionPlan.create("s", OperatingMode.ORGANIZE, [PlanAction("trash", str(source), None, source.stat().st_size, "test", RiskClass.REVERSIBLE)], "test")
    with pytest.raises(PolicyError):
        PlanExecutor(approvals, trash, audit).apply(plan, "not-a-token", phone)
    assert source.exists()

def test_approved_reversible_action(tmp_path, phone):
    approvals, trash, audit = services(tmp_path, phone)
    source = phone / "Download/old-installer.apk"
    plan = ActionPlan.create("s", OperatingMode.ORGANIZE, [PlanAction("trash", str(source), None, source.stat().st_size, "test", RiskClass.REVERSIBLE)], "test")
    token, _ = approvals.approve(plan, "APPROVE")
    ids = PlanExecutor(approvals, trash, audit).apply(plan, token, phone)
    assert len(ids) == 1 and not source.exists()
    restored = trash.restore(ids[0])
    assert restored.exists()

def test_changed_plan_after_approval_blocked(tmp_path, phone):
    approvals, trash, audit = services(tmp_path, phone)
    source = phone / "Download/old-installer.apk"
    plan = ActionPlan.create("s", OperatingMode.ORGANIZE, [PlanAction("trash", str(source), None, source.stat().st_size, "test", RiskClass.REVERSIBLE)], "test")
    token, _ = approvals.approve(plan, "APPROVE")
    plan.actions[0].size += 1
    with pytest.raises(PolicyError, match="changed"):
        PlanExecutor(approvals, trash, audit).apply(plan, token, phone)

def test_protected_comptext_action_blocked_even_with_token(tmp_path, phone):
    approvals, trash, audit = services(tmp_path, phone)
    source = phone / "CompText/critical-project.zip"
    plan = ActionPlan.create("s", OperatingMode.ORGANIZE, [PlanAction("trash", str(source), None, source.stat().st_size, "test", RiskClass.REVERSIBLE)], "test")
    token, _ = approvals.approve(plan, "APPROVE")
    with pytest.raises(PermissionError):
        PlanExecutor(approvals, trash, audit).apply(plan, token, phone)
    assert source.exists()
