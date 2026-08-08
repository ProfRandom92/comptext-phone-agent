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

    assert "pull_request:" in text
    assert ".github/workflows/release.yml" in text
    assert "github.event.pull_request.head.repo.full_name == github.repository" in text
    assert "RELEASE_VERSION: ${{ inputs.version || '0.6.1' }}" in text

    assert "permissions:\n      contents: read\n      id-token: write\n      attestations: write\n      artifact-metadata: write" in text

    assert "anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610" in text
    assert "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6" in text

    assert text.index("Package and verify release") < text.index("Generate release SBOM")
    assert "SUPPLY_CHAIN_SHA256SUMS" in text
    assert "Generate build provenance attestation" in text
    assert "Generate SBOM attestation" in text
    assert "subject-path: .dist/*" in text
    assert "sbom-path: .dist/comptext-phone-agent-${{ env.RELEASE_VERSION }}-full.spdx.json" in text


def test_security_ci_covers_python_and_kotlin_codeql_with_strict_build() -> None:
    path = Path(".github/workflows/security-ci.yml")
    text = path.read_text(encoding="utf-8")
    pin = "github/codeql-action/"
    sha = "@e4fba868fa4b1b91e1fdab776edc8cfbe6e9fb81"

    assert text.count(pin) >= 2
    for line in text.splitlines():
        if pin in line:
            assert sha in line

    assert "security-events: write" in text
    assert "contents: write" not in text
    assert "write-all" not in text
    assert "language: python" in text
    assert "build-mode: none" in text
    assert "language: java-kotlin" in text
    assert "build-mode: manual" in text
    assert "queries: security-extended" in text
    assert 'java-version: "21"' in text
    assert ":app:compileDebugKotlin --dependency-verification strict --no-daemon --console=plain" in text


def test_dependabot_covers_all_maintained_dependency_ecosystems() -> None:
    path = Path(".github/dependabot.yml")
    assert path.is_file()
    text = path.read_text(encoding="utf-8")

    assert 'package-ecosystem: "pip"' in text
    assert 'directory: "/"' in text
    assert 'package-ecosystem: "gradle"' in text
    assert 'directory: "/android-broker"' in text
    assert 'package-ecosystem: "github-actions"' in text
    assert "auto-merge" not in text.casefold()
