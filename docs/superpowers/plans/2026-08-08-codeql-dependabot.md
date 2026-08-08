# CodeQL and Dependabot Hardening Plan

> Use TDD and verification-before-completion. Keep this PR stacked on the supply-chain PR and do not merge it automatically.

## Task 1: Define security workflow regressions

**File:** `tests/unit/test_workflow_security.py`

- [x] Assert every CodeQL action use is pinned to `e4fba868fa4b1b91e1fdab776edc8cfbe6e9fb81`.
- [x] Assert CodeQL permissions include read-only contents plus job-scoped `security-events: write`.
- [x] Assert language matrix contains Python `none` and Java/Kotlin `manual`.
- [x] Assert Kotlin build uses JDK 21 and strict Gradle dependency verification.
- [x] Assert `security-extended` queries are enabled.
- [x] Assert Dependabot config contains `pip`, `gradle`, and `github-actions` update blocks.
- [x] Run the tests before implementation and confirm RED.

RED evidence: 220 existing tests passed; exactly two new security-contract tests failed because CodeQL/Dependabot had not been added.

## Task 2: Add CodeQL advanced setup to established Security CI

**File:** `.github/workflows/security-ci.yml`

A separate new `codeql.yml` was initially drafted, then removed before final verification because a workflow introduced for the first time on a stacked PR is not a reliable self-validation path. Integrating CodeQL into the existing Security CI means the real CodeQL jobs execute on this PR immediately.

- [x] Add weekly schedule to existing Security CI while retaining PR, `main` push, and manual triggers.
- [x] Keep top-level `contents: read`.
- [x] Keep the existing defensive job explicitly `contents: read` only.
- [x] Add CodeQL matrix job with `contents: read` + `security-events: write` only.
- [x] Pin checkout/setup-java/setup-gradle/CodeQL actions by full SHA.
- [x] Use Python `none` and Java/Kotlin `manual` build modes.
- [x] Initialize CodeQL with `security-extended` queries.
- [x] For Java/Kotlin, set up JDK 21 and Gradle, chmod wrapper, and run `:app:compileDebugKotlin --dependency-verification strict --no-daemon --console=plain` from `android-broker`.
- [x] Analyze and upload SARIF through the pinned CodeQL Action.

## Task 3: Add Dependabot

**File:** `.github/dependabot.yml`

- [x] Add weekly pip updates at `/`.
- [x] Add weekly Gradle updates at `/android-broker`.
- [x] Add weekly GitHub Actions updates at `/`.
- [x] Use bounded open-PR limits and no auto-merge configuration.

## Task 4: Verify

- [ ] Existing Python 3.12/3.13/3.14 CI succeeds on the final head.
- [ ] Defensive Security CI job succeeds.
- [ ] CodeQL Python analysis succeeds.
- [ ] CodeQL Java/Kotlin analysis succeeds with strict Gradle verification.
- [ ] Workflow pin/permission guard succeeds.
- [ ] Inspect CodeQL results for newly surfaced alerts before marking ready.
- [ ] Update PR with exact run evidence and leave unmerged.
