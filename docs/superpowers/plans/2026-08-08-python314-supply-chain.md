# Python 3.14 and Supply-Chain Hardening Plan

> Use TDD and verification-before-completion. No merge or release publication is part of this plan.

**Goal:** Test the current Termux-era Python version and add additive SBOM + signed provenance evidence to the non-publishing manual release workflow.

## Task 1: Define the workflow contract in tests

**File:** `tests/unit/test_workflow_security.py`

- [ ] Assert Python CI matrix contains `3.12`, `3.13`, and `3.14`.
- [ ] Assert manual release workflow pins Anchore SBOM action v0.24.0 by full SHA.
- [ ] Assert manual release workflow pins `actions/attest` v4.2.2 by full SHA.
- [ ] Assert top-level release permissions remain `contents: read`.
- [ ] Assert job-level attestation permissions are limited to `contents: read`, `id-token: write`, `attestations: write`, and `artifact-metadata: write`.
- [ ] Assert no `write-all` or `contents: write` permission is introduced.
- [ ] Assert packaging/standalone verification occurs before SBOM generation.
- [ ] Assert provenance and SBOM attestation steps exist.
- [ ] Run RED CI before changing workflows.

## Task 2: Add Python 3.14 CI

**File:** `.github/workflows/python-ci.yml`

- [ ] Extend the matrix to Python 3.14.
- [ ] Do not special-case or skip tests on 3.14.
- [ ] Run the same install, guard, compile/test, diagnostics, dashboard, and installation verification path.
- [ ] Diagnose any 3.14 failure before changing dependencies.

## Task 3: Generate release SBOM

**File:** `.github/workflows/release.yml`

- [ ] Keep the established release packaging and standalone verification step unchanged and before supply-chain generation.
- [ ] Run `anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610` against the verified full ZIP.
- [ ] Write SPDX JSON into `.dist/comptext-phone-agent-${version}-full.spdx.json`.
- [ ] Disable the action's separate workflow-artifact and release-asset uploads.
- [ ] Create `.dist/SUPPLY_CHAIN_SHA256SUMS` for the final evidence files.

## Task 4: Add signed GitHub attestations

**File:** `.github/workflows/release.yml`

- [ ] Add job-scoped `id-token: write`, `attestations: write`, and `artifact-metadata: write`, retaining `contents: read`.
- [ ] Generate build provenance for `.dist/*` with `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6`.
- [ ] Generate an SBOM attestation binding the full ZIP to the generated SPDX JSON SBOM with the same pinned action.
- [ ] Keep the existing `.dist/*` upload as the final artifact upload.

## Task 5: Verify

- [ ] Python 3.12 succeeds.
- [ ] Python 3.13 succeeds.
- [ ] Python 3.14 succeeds.
- [ ] Security CI succeeds.
- [ ] Workflow pin/permission guard succeeds.
- [ ] Manual Release succeeds on the exact PR head without publishing a release.
- [ ] Uploaded artifact contains the six core release files plus SBOM and supply-chain checksum evidence.
- [ ] Core `SHA256SUMS` still validates the original release contract.
- [ ] `SUPPLY_CHAIN_SHA256SUMS` validates all additive evidence subjects listed within it.
- [ ] GitHub records provenance and SBOM attestations for the run.

## Task 6: Review/handoff

- [ ] Update draft PR with exact workflow runs and artifact/attestation evidence.
- [ ] Attempt CodeRabbit review if the CLI runtime is available; otherwise record the concrete environment failure rather than inventing a review.
- [ ] Leave the PR stacked and unmerged.
- [ ] Inspect repository security/protection settings separately after this PR is verified.
