from pathlib import Path
import pytest
from comptext_phone_agent.approvals.engine import ApprovalEngine
from comptext_phone_agent.approvals.policy import PolicyError, require_mode
from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.models import ActionPlan, OperatingMode, PlanAction, RiskClass

def engine(tmp_path):
    db = Database(tmp_path / "state.db")
    return ApprovalEngine(db, tmp_path / "data")

def plan():
    return ActionPlan.create("session-a", OperatingMode.ORGANIZE, [PlanAction("trash", "/tmp/a.zip", None, 10, "test", RiskClass.REVERSIBLE)], "test plan")

def test_valid_approval(tmp_path):
    service = engine(tmp_path); value = plan()
    token, claims = service.approve(value, "APPROVE")
    verified = service.verify(token, value)
    assert verified.approval_id == claims.approval_id

def test_wrong_phrase(tmp_path):
    with pytest.raises(PolicyError):
        engine(tmp_path).approve(plan(), "yes")

def test_invalid_signature(tmp_path):
    service = engine(tmp_path); value = plan()
    token, _ = service.approve(value, "APPROVE")
    changed = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(PolicyError):
        service.verify(changed, value)

def test_expired_token(tmp_path):
    service = engine(tmp_path); value = plan()
    token, _ = service.approve(value, "APPROVE", ttl_seconds=-1)
    with pytest.raises(PolicyError, match="expired"):
        service.verify(token, value)

def test_plan_change_invalidates(tmp_path):
    service = engine(tmp_path); value = plan()
    token, _ = service.approve(value, "APPROVE")
    value.description = "changed"
    with pytest.raises(PolicyError, match="changed"):
        service.verify(token, value)

def test_token_single_use(tmp_path):
    service = engine(tmp_path); value = plan()
    token, _ = service.approve(value, "APPROVE")
    service.verify(token, value)
    with pytest.raises(PolicyError, match="already used"):
        service.verify(token, value)

def test_risk3_phrase(tmp_path):
    value = ActionPlan.create("s", OperatingMode.CONTROLLED, [PlanAction("purge", "/tmp/a", None, 1, "purge", RiskClass.IRREVERSIBLE)], "purge")
    with pytest.raises(PolicyError):
        engine(tmp_path).approve(value, "APPROVE")
    token, _ = engine(tmp_path / "second").approve(value, "DELETE PERMANENTLY")
    assert token

def test_analysis_mode_blocks_changes():
    with pytest.raises(PolicyError):
        require_mode(OperatingMode.ANALYSIS, RiskClass.REVERSIBLE)
