from pathlib import Path
import pytest
from comptext_phone_agent.backup.planner import BackupPlanner
from comptext_phone_agent.backup.rclone import RcloneClient, RcloneError
from comptext_phone_agent.config import load_config
from comptext_phone_agent.storage.exclusions import ExclusionEngine

def engine():
    return ExclusionEngine(load_config(Path("/missing")).exclusions)

def test_backup_plan_and_dry_run(phone):
    plan = BackupPlanner(engine()).plan([phone / "Download/recent.zip"], "nextcloud:Phone")
    result = RcloneClient("definitely-missing-rclone", exclusions=engine()).apply(plan, dry_run=True)
    assert result.dry_run and result.returncode == 0

def test_missing_rclone_on_execute(phone):
    plan = BackupPlanner(engine()).plan([phone / "Download/recent.zip"], "nextcloud:Phone")
    with pytest.raises(RcloneError, match="not installed"):
        RcloneClient("definitely-missing-rclone", exclusions=engine()).apply(plan, dry_run=False)

def test_protected_upload_rejected(phone):
    with pytest.raises(PermissionError):
        BackupPlanner(engine()).plan([phone / "CompText/critical-project.zip"], "drive:Backup")

def test_backup_plan_never_deletes(phone):
    file = phone / "Download/recent.zip"
    plan = BackupPlanner(engine()).plan([file], "drive:Backup")
    RcloneClient("missing", exclusions=engine()).apply(plan, dry_run=True)
    assert file.exists()

def test_local_backup_executes_with_hash_verification(phone, tmp_path):
    source=phone/'Download/recent.zip'; target=tmp_path/'local-backup'
    plan=BackupPlanner(engine()).plan([source],str(target))
    result=RcloneClient(exclusions=engine()).apply(plan,dry_run=False)
    assert result.copied and result.verified and (target/source.name).read_bytes()==source.read_bytes()
    assert source.exists()

def test_local_backup_collision_skip(phone,tmp_path):
    source=phone/'Download/recent.zip'; target=tmp_path/'local-backup'; target.mkdir()
    (target/source.name).write_bytes(b'existing')
    plan=BackupPlanner(engine()).plan([source],str(target))
    result=RcloneClient(exclusions=engine(),conflict_strategy='skip').apply(plan,dry_run=False)
    assert result.skipped and (target/source.name).read_bytes()==b'existing'
