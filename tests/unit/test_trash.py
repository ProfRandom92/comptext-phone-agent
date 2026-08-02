from pathlib import Path
from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.config import load_config
from comptext_phone_agent.storage.exclusions import ExclusionEngine
from comptext_phone_agent.storage.trash import TrashManager
import pytest

def manager(tmp_path, phone):
    return TrashManager(phone / ".CompTextTrash", Database(tmp_path / "state.db"), ExclusionEngine(load_config(Path("/missing")).exclusions))

def test_move_and_restore(tmp_path, phone):
    service = manager(tmp_path, phone)
    source = phone / "Download/old-installer.apk"
    item_id = service.move(source, "approval", phone)
    assert not source.exists()
    item = service.list()[0]
    assert item["sha256"] and Path(item["trash_path"]).exists()
    restored = service.restore(item_id)
    assert restored.exists() and restored == source

def test_restore_collision(tmp_path, phone):
    service = manager(tmp_path, phone)
    source = phone / "Download/archive-old.zip"
    item_id = service.move(source, "approval", phone)
    source.write_text("new file", encoding="utf-8")
    restored = service.restore(item_id)
    assert restored != source
    assert restored.exists()

def test_comptext_move_blocked(tmp_path, phone):
    service = manager(tmp_path, phone)
    with pytest.raises(PermissionError):
        service.move(phone / "CompText/critical-project.zip", "approval", phone)

def test_purge_removes_file(tmp_path, phone):
    service = manager(tmp_path, phone)
    item_id = service.move(phone / "Download/old-installer.apk", "approval", phone)
    path = Path(service.list()[0]["trash_path"])
    assert service.purge([item_id], "risk3") == 1
    assert not path.exists()
