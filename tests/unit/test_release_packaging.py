from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
import zipfile

import pytest

from scripts.package_release import (
    ReleaseError,
    build_release,
    select_release_files,
    verify_zip,
    write_deterministic_zip,
)


def test_release_file_sets_are_explicit_and_distinct() -> None:
    paths = {
        ".github/workflows/ci.yml",
        "README.md",
        "pyproject.toml",
        "src/comptext_phone_agent/__init__.py",
        "tests/unit/test_example.py",
        "android-broker/app/build.gradle.kts",
        "docs/verification.md",
        "config/default.yaml",
        "scripts/package_release.py",
        "install-termux.sh",
    }

    full = select_release_files("full", paths)
    source = select_release_files("source", paths)
    upgrade = select_release_files("upgrade", paths)

    assert full == paths
    assert "android-broker/app/build.gradle.kts" in source
    assert "tests/unit/test_example.py" in source
    assert "docs/verification.md" not in source
    assert "src/comptext_phone_agent/__init__.py" in upgrade
    assert "install-termux.sh" in upgrade
    assert "android-broker/app/build.gradle.kts" not in upgrade
    assert len({frozenset(full), frozenset(source), frozenset(upgrade)}) == 3


def test_deterministic_zip_has_safe_prefix_modes_crc_and_bytes(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    script = root / "install-termux.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    readme_hash = hashlib.sha256((root / "README.md").read_bytes()).hexdigest()
    script_hash = hashlib.sha256(script.read_bytes()).hexdigest()
    modes = {"README.md": 0o644, "install-termux.sh": 0o755}
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    write_deterministic_zip(root, first, modes.keys(), modes, "comptext-phone-agent-0.6.1")
    script.touch()
    write_deterministic_zip(root, second, modes.keys(), modes, "comptext-phone-agent-0.6.1")

    assert first.read_bytes() == second.read_bytes()
    assert verify_zip(first, "comptext-phone-agent-0.6.1") == {
        "comptext-phone-agent-0.6.1/README.md": readme_hash,
        "comptext-phone-agent-0.6.1/install-termux.sh": script_hash,
    }
    with zipfile.ZipFile(first) as archive:
        by_name = {item.filename: item for item in archive.infolist()}
        assert (by_name["comptext-phone-agent-0.6.1/install-termux.sh"].external_attr >> 16) & 0o777 == 0o755


def test_zip_verifier_rejects_traversal_and_forbidden_artifacts(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../secret", "x")
    with pytest.raises(ReleaseError, match="unsafe archive path"):
        verify_zip(traversal, "comptext-phone-agent-0.6.1")

    model = tmp_path / "model.zip"
    with zipfile.ZipFile(model, "w") as archive:
        archive.writestr("comptext-phone-agent-0.6.1/models/router.litertlm", "x")
    with pytest.raises(ReleaseError, match="forbidden archive member"):
        verify_zip(model, "comptext-phone-agent-0.6.1")


def test_install_verifier_preserves_rollback_tree_without_copying_unreadable_files() -> None:
    script = (Path(__file__).parents[2] / "scripts" / "verify_release_install.sh").read_text(encoding="utf-8")

    assert 'cp -a "$install_root" "$backup_root"' not in script
    assert 'mv "$install_root" "$backup_root"' in script
    assert script.count('bash "$install_root/install-termux.sh" --sandbox') == 2


def test_build_release_embeds_current_git_commit_in_full_archive(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    apk = tmp_path / "app-debug.apk"
    apk.write_bytes(b"synthetic-apk")
    output = tmp_path / "dist"

    build_release(root, output, apk, "0.6.1")

    expected_commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    manifest = json.loads((output / "release-manifest.json").read_text(encoding="utf-8"))
    full_zip = output / "comptext-phone-agent-0.6.1-full.zip"
    with zipfile.ZipFile(full_zip) as archive:
        embedded_commit = archive.read(
            "comptext-phone-agent-0.6.1/RELEASE_COMMIT.txt"
        ).decode("ascii").strip()

    assert manifest["git_commit"] == expected_commit
    assert embedded_commit == expected_commit


def test_zip_verifier_rejects_mismatched_expected_member(tmp_path: Path) -> None:
    archive_path = tmp_path / "release.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("comptext-phone-agent-0.6.1/RELEASE_COMMIT.txt", "stale\n")

    with pytest.raises(ReleaseError, match="release metadata mismatch"):
        verify_zip(
            archive_path,
            "comptext-phone-agent-0.6.1",
            expected_members={"RELEASE_COMMIT.txt": b"current\n"},
        )
