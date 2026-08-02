from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

import pytest

from scripts.package_release import (
    ReleaseError,
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
