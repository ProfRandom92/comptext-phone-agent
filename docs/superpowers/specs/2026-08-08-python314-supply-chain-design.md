# Python 3.14 and Supply-Chain Hardening Design

## Goal

Add first-class Python 3.14 compatibility evidence and strengthen non-publishing release provenance with a generated SBOM plus GitHub/Sigstore artifact attestations.

## Context

The primary Android/Termux target now ships Python 3.14.x. The core intentionally stays on `pydantic==1.10.25`, whose release notes include minimal Python 3.14 support. The CI matrix therefore needs to exercise the interpreter version users receive on current Termux instead of stopping at Python 3.13.

The existing manual release workflow already builds and independently verifies deterministic archives, the Android debug APK, `release-manifest.json`, and `SHA256SUMS`. It does not publish a GitHub Release. This makes it the appropriate place to add supply-chain evidence without changing normal PR permissions.

## Python compatibility

Python CI expands from 3.12/3.13 to 3.12/3.13/3.14. All existing tests, dashboard integration tests, diagnostics, and installation verification run on 3.14 exactly as they do on the existing matrix.

No runtime dependency is upgraded merely to make 3.14 green. Any failure is diagnosed as a real compatibility issue first.

## SBOM

The manual release workflow generates an SPDX JSON SBOM from the verified full release archive using Anchore `sbom-action` / Syft.

Pinned action:

- `anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610` (`v0.24.0`)

The SBOM is written into `.dist` with a deterministic release-specific name and is not independently uploaded by the action. The existing release artifact upload remains the single artifact container for the complete `.dist` directory.

The original six-file release contract stays unchanged and is verified before SBOM creation. Supply-chain evidence is additive and generated afterward so the established release verifier cannot silently accept a different core release contract.

## Provenance attestations

GitHub's consolidated `actions/attest` action generates signed attestations backed by short-lived Sigstore certificates and the GitHub OIDC identity.

Pinned action:

- `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6` (`v4.2.2`)

Two attestations are generated:

1. **Build provenance** for all files present in `.dist` after SBOM/checksum generation.
2. **SBOM attestation** binding the SPDX SBOM to the full release ZIP it describes.

## Permission model

Top-level workflow permissions remain `contents: read`.

Only the manual release `package` job receives the additional permissions required to mint and store attestations:

- `contents: read`
- `id-token: write`
- `attestations: write`
- `artifact-metadata: write`

No `contents: write`, `actions: write`, `packages: write`, or `write-all` permission is granted. The workflow still cannot publish a release, push a tag, modify source, or overwrite repository contents.

## Supply-chain checksum

After SBOM generation the workflow creates `.dist/SUPPLY_CHAIN_SHA256SUMS` over the complete evidence set, excluding that checksum file itself. This supplements the core `SHA256SUMS` without changing its semantics.

## Test strategy

TDD regressions assert that:

1. Python CI includes 3.14 alongside 3.12 and 3.13;
2. both new actions are pinned to exact reviewed SHAs;
3. top-level permissions remain read-only;
4. expanded write permissions are scoped to the manual release job;
5. no `contents: write` or `write-all` permission appears;
6. release verification happens before SBOM generation;
7. provenance and SBOM attestations are present;
8. the release artifact upload still includes `.dist/*`.

## Non-goals

This PR does not publish a GitHub Release, create or move a tag, merge its parent dashboard PR, enable repository settings, or change signing keys. Repository branch/security settings are reviewed separately after the workflow hardening is verified.
