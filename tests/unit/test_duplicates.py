from pathlib import Path
from comptext_phone_agent.config import load_config
from comptext_phone_agent.storage.duplicates import DuplicateDetector
from comptext_phone_agent.storage.exclusions import ExclusionEngine
from comptext_phone_agent.storage.scanner import StorageScanner

def groups(phone):
    cfg = load_config(Path("/missing"))
    result = StorageScanner(ExclusionEngine(cfg.exclusions)).scan(phone)
    return DuplicateDetector().find(result, verify=True)

def test_identical_content_detected(phone):
    values = groups(phone)
    assert any(x.kind == "same_content_different_name" and len(x.files) == 2 for x in values)

def test_same_name_different_content(phone):
    assert any(x.kind == "same_name_different_content" for x in groups(phone))

def test_protected_duplicate_marked(phone):
    group = next(x for x in groups(phone) if x.kind == "same_content_different_name")
    assert any("DCIM" in x for x in group.protected)

def test_different_content_not_exact_duplicate(phone):
    exact_paths = [set(x.files) for x in groups(phone) if x.sha256]
    assert not any(any("Documents/same-name.zip" in p for p in group) and any("Download/same-name.zip" in p for p in group) for group in exact_paths)
