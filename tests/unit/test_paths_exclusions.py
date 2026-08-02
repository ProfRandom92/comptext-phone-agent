from pathlib import Path
import pytest
from comptext_phone_agent.config import load_config
from comptext_phone_agent.paths import PathSecurityError, ensure_no_symlink_escape, normalize_path
from comptext_phone_agent.storage.exclusions import ExclusionEngine

def test_path_outside_root_rejected(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    outside = tmp_path / "outside"; outside.write_text("x")
    with pytest.raises(PathSecurityError):
        normalize_path(outside, [root], must_exist=True)

def test_path_inside_root_allowed(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    child = root / "x"; child.write_text("x")
    assert normalize_path(child, [root], must_exist=True) == child.resolve()

def test_symlink_escape_rejected(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    outside = tmp_path / "outside"; outside.write_text("secret")
    link = root / "link"; link.symlink_to(outside)
    with pytest.raises(PathSecurityError):
        ensure_no_symlink_escape(link, root)

def test_comptext_relative_path_protected(phone):
    engine = ExclusionEngine(load_config(Path("/missing")).exclusions)
    decision = engine.evaluate(phone / "CompText/critical-project.zip", phone)
    assert decision.protected and decision.never_upload

def test_repo_ancestor_does_not_protect_unrelated_file(phone):
    engine = ExclusionEngine(load_config(Path("/missing")).exclusions)
    decision = engine.evaluate(phone / "Download/old-installer.apk", phone)
    assert not decision.protected

def test_env_file_redacted_by_exclusion(tmp_path):
    engine = ExclusionEngine(load_config(Path("/missing")).exclusions)
    env = tmp_path / ".env"; env.write_text("KEY=x")
    assert engine.evaluate(env, tmp_path).protected
