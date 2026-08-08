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


def test_python_ci_covers_current_termux_python() -> None:
    text = Path(".github/workflows/python-ci.yml").read_text(encoding="utf-8")
    assert 'python-version: ["3.12", "3.13", "3.14"]' in text


def test_manual_release_has_scoped_supply_chain_hardening() -> None:
    text = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "permissions:\n  contents: read" in text
    assert "contents: write" not in text
    assert "write-all" not in text

    assert "permissions:\n      contents: read\n      id-token: write\n      attestations: write\n      artifact-metadata: write" in text

    assert "anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610" in text
    assert "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6" in text

    assert text.index("Package and verify release") < text.index("Generate release SBOM")
    assert "SUPPLY_CHAIN_SHA256SUMS" in text
    assert "Generate build provenance attestation" in text
    assert "Generate SBOM attestation" in text
    assert "subject-path: .dist/*" in text
    assert "sbom-path: .dist/comptext-phone-agent-${{ inputs.version }}-full.spdx.json" in text
