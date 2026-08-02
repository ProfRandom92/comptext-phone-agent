from __future__ import annotations

from pathlib import Path

from scripts.check_workflow_pins import scan_workflow, scan_workflows


def test_repository_workflows_use_full_pins_and_least_permissions() -> None:
    root = Path(__file__).parents[2]
    assert scan_workflows(root) == []


def test_workflow_guard_rejects_tag_and_missing_permissions(tmp_path: Path) -> None:
    workflow = tmp_path / "unsafe.yml"
    workflow.write_text(
        "name: unsafe\non: push\njobs:\n  test:\n    steps:\n      - uses: actions/checkout@v7\n",
        encoding="utf-8",
    )
    findings = scan_workflow(workflow)
    assert any("not pinned" in finding for finding in findings)
    assert any("permissions" in finding for finding in findings)
