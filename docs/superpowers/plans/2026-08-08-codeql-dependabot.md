# CodeQL and Dependabot Hardening Plan

> Use TDD and verification-before-completion. Keep this PR stacked on the supply-chain PR and do not merge it automatically.

## Task 1: Define security workflow regressions

**File:** `tests/unit/test_workflow_security.py`

- [ ] Assert `.github/workflows/codeql.yml` exists.
- [ ] Assert every CodeQL action use is pinned to `e4fba868fa4b1b91e1fdab776edc8cfbe6e9fb81`.
- [ ] Assert CodeQL permissions are exactly read-only contents plus `security-events: write`.
- [ ] Assert language matrix contains Python `none` and Java/Kotlin `manual`.
- [ ] Assert Kotlin build uses JDK 21 and strict Gradle dependency verification.
- [ ] Assert `security-extended` queries are enabled.
- [ ] Assert Dependabot config contains `pip`, `gradle`, and `github-actions` update blocks.
- [ ] Run the tests before adding workflows and confirm RED.

## Task 2: Add CodeQL advanced setup

**File:** `.github/workflows/codeql.yml`

- [ ] Trigger on PRs, pushes to `main`, weekly schedule, and manual dispatch.
- [ ] Pin checkout/setup-java/setup-gradle/CodeQL actions by full SHA.
- [ ] Use a matrix with Python `none` and Java/Kotlin `manual`.
- [ ] Initialize CodeQL with `security-extended` queries.
- [ ] For Java/Kotlin only, set up JDK 21 and Gradle, chmod wrapper, and run `:app:compileDebugKotlin --dependency-verification strict --no-daemon --console=plain` from `android-broker`.
- [ ] Analyze and upload SARIF with `security-events: write` only.

## Task 3: Add Dependabot

**File:** `.github/dependabot.yml`

- [ ] Add weekly pip updates at `/`.
- [ ] Add weekly Gradle updates at `/android-broker`.
- [ ] Add weekly GitHub Actions updates at `/`.
- [ ] Use bounded open-PR limits and no auto-merge configuration.

## Task 4: Verify

- [ ] Existing Python 3.12/3.13/3.14 CI succeeds.
- [ ] Existing Security CI succeeds.
- [ ] CodeQL Python analysis succeeds.
- [ ] CodeQL Java/Kotlin analysis succeeds with strict Gradle verification.
- [ ] Workflow pin/permission guard succeeds.
- [ ] Inspect CodeQL results for any newly surfaced alerts before marking ready.
- [ ] Update PR with exact run evidence and leave unmerged.
