import time
from pathlib import Path
from comptext_phone_agent.config import load_config
from comptext_phone_agent.storage.analyzer import StorageAnalyzer
from comptext_phone_agent.storage.exclusions import ExclusionEngine
from comptext_phone_agent.storage.scanner import StorageScanner

def result(phone):
    cfg = load_config(Path("/missing"))
    return StorageScanner(ExclusionEngine(cfg.exclusions)).scan(phone)

def test_scan_finds_files(phone):
    scan = result(phone)
    assert scan.total_files >= 12
    assert scan.total_size > 8 * 1024 * 1024

def test_categories(phone):
    scan = result(phone)
    categories = {x.category for x in scan.files}
    assert {"video", "apk", "archive", "image", "audio", "document"} <= categories

def test_largest_file(phone):
    largest = StorageAnalyzer(result(phone)).largest_files(1)[0]
    assert largest.name == "large-demo-video.mkv"

def test_old_files_use_mtime(phone):
    old = StorageAnalyzer(result(phone)).old_files(365)
    names = {x.name for x in old}
    assert "old-installer.apk" in names
    assert "recent.zip" not in names

def test_empty_file(phone):
    names = {x.name for x in StorageAnalyzer(result(phone)).empty_files()}
    assert "empty.txt" in names

def test_type_totals(phone):
    data = StorageAnalyzer(result(phone)).by_type()
    assert data["archive"]["count"] >= 4

def test_protected_file_record(phone):
    item = next(x for x in result(phone).files if x.name == "critical-project.zip")
    assert item.exclusion_reason

def test_symlink_not_followed(phone):
    link = next((x for x in result(phone).files if x.name == "outside-link.txt"), None)
    if link:
        assert link.is_symlink
        assert link.exclusion_reason == "symlink not followed"
