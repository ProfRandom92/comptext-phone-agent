from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.check_forbidden_tracked_files import path_reason


SCRIPT = Path(__file__).parents[2] / "scripts" / "check_forbidden_tracked_files.py"


def run_guard(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )


def initialize_repo(tmp_path: Path, relative_path: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    tracked = repo / relative_path
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("fixture", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo), "add", "-f", relative_path],
        check=True,
    )
    return repo


def test_guard_accepts_safe_tracked_source(tmp_path: Path) -> None:
    repo = initialize_repo(tmp_path, "src/example.py")

    result = run_guard(repo)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "tracked-file guard: ok"


@pytest.mark.parametrize(
    "relative_path",
    [
        ".env",
        ".venv/lib/site.py",
        "android-broker/local.properties",
        "build/output.txt",
        "model/router.litertlm",
        "release/app.apk",
        "release/debug.keystore",
        "runtime/state.sqlite3",
        "src/module.py.before-fix",
    ],
)
def test_guard_rejects_forbidden_tracked_file(
    relative_path: str,
) -> None:
    assert path_reason(relative_path) is not None


def test_guard_reports_secret_path_without_echoing_secret(tmp_path: Path) -> None:
    secret = "ghp_" + "A" * 36
    repo = initialize_repo(tmp_path, "src/settings.py")
    (repo / "src/settings.py").write_text(
        f'TOKEN = "{secret}"',
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "-C", str(repo), "add", "-f", "src/settings.py"],
        check=True,
    )

    result = run_guard(repo)

    assert result.returncode == 1
    assert "src/settings.py" in result.stderr.replace("\\", "/")
    assert secret not in result.stderr


def test_guard_rejects_large_tracked_binary(tmp_path: Path) -> None:
    repo = initialize_repo(tmp_path, "assets/blob.bin")
    with (repo / "assets/blob.bin").open("wb") as handle:
        handle.seek(5 * 1024 * 1024)
        handle.write(b"x")
    subprocess.run(
        ["git", "-C", str(repo), "add", "-f", "assets/blob.bin"],
        check=True,
    )

    result = run_guard(repo)

    assert result.returncode == 1
    assert "assets/blob.bin" in result.stderr.replace("\\", "/")
