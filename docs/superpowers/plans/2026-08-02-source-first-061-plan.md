# CompText Phone Agent 0.6.1 Source-first Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` or `superpowers:executing-plans`.

**Goal:** Import the full 0.6.1 source into the empty private repository, preserve all
functionality, harden provider/orchestrator boundaries, add the Android LiteRT-LM broker,
and produce a verified release.

**Architecture:** Preserve the existing Python/Termux product as the policy and execution
authority. Add an authenticated loopback-only Android inference companion behind a narrow
protocol. Work from an immutable baseline commit and use TDD for each improvement.

**Tech Stack:** Python 3.12/3.13, Typer, Textual, Pydantic-compatible validation, SQLite,
httpx, Kotlin, Gradle Kotlin DSL, Android API 31+, Coroutines, Android Keystore, SAF,
LiteRT-LM, GitHub Actions.

## Global constraints

- Repository remains private.
- Full 0.6.1 archive is authoritative.
- Existing tests may not be replaced with a smaller suite.
- No model files, secrets, keystores, databases, SDK paths, or build outputs in Git.
- No cloud/model fallback without explicit user choice.
- Broker binds only to `127.0.0.1`.
- Preview/read-only is the default.

---

### Task 1: Verify and compare source archives

**Files:**
- Create: `docs/reconstruction/archive-inventory.json`
- Create: `docs/reconstruction/archive-comparison.md`
- Use: `scripts/preflight_source_audit.py`

- [ ] Run the audit script for all three archives.
- [ ] Confirm expected SHA-256 and CRC.
- [ ] Compare normalized file paths and SHA-256 per file.
- [ ] Record files unique to each archive.
- [ ] Reject path traversal and unsafe archive members.
- [ ] Commit the inventory documentation.

### Task 2: Create immutable baseline import

**Files:**
- Import: full extracted source tree
- Create/modify: `.gitignore`
- Create: `docs/reconstruction/baseline-import.md`

- [ ] Extract to a clean staging directory.
- [ ] Remove only generated/unsafe items identified by Task 1.
- [ ] Run secret, binary, model, keystore, and database scans.
- [ ] Run `python -m compileall src`.
- [ ] Install in a compatible Python environment and run full pytest.
- [ ] Record Python and dependency versions.
- [ ] Commit to `main` with `chore: import verified CompText Phone Agent 0.6.1 baseline`.
- [ ] Tag the baseline locally as `baseline-0.6.1-source-import`.

### Task 3: Establish feature worktree and harness

**Files:**
- Create: `.githooks/pre-commit`
- Create: `.githooks/pre-push`
- Create: `scripts/install-git-hooks.sh`
- Create: `AGENTS.md`
- Create: `android-broker/AGENTS.md`

- [ ] Create branch `feature/phone-agent-061-hardening`.
- [ ] Create isolated worktree.
- [ ] Install versioned hooks.
- [ ] Keep pre-commit fast and pre-push changed-path aware.
- [ ] Add tests for forbidden tracked files.
- [ ] Commit.

### Task 4: Fix version reporting

**Files:**
- Modify: `src/comptext_phone_agent/chat_entry.py`
- Modify: `src/comptext_phone_agent/agent/terminal_chat.py`
- Modify: any banner/version helpers
- Test: new focused unit/CLI tests

- [ ] Write tests proving the banner reads installed package version.
- [ ] Verify the tests fail on hard-coded `0.3`.
- [ ] Implement one shared version helper using `importlib.metadata`.
- [ ] Remove all stale hard-coded application versions.
- [ ] Run focused and full tests.
- [ ] Commit `fix: report installed package version consistently`.

### Task 5: Centralize Ollama/provider configuration

**Files:**
- Inspect/modify:
  - `src/comptext_phone_agent/agent/ollama_client.py`
  - `src/comptext_phone_agent/ollama_chat.py`
  - `src/comptext_phone_agent/runtime/ollama_model.py`
  - `src/comptext_phone_agent/config.py`
  - CLI/TUI provider display
- Tests: provider precedence and HTTP failures

- [ ] Inventory every model/provider default.
- [ ] Write precedence tests: CLI → config → environment → fallback.
- [ ] Write tests that Qwen Pro-only is not the fallback.
- [ ] Write 401/403/404/429/timeout/network tests.
- [ ] Implement one immutable effective-provider configuration object.
- [ ] Remove duplicate hard-coded defaults.
- [ ] Never silently switch models.
- [ ] Show effective provider/model without exposing keys.
- [ ] Keep keyword orchestrator functional with no cloud credentials.
- [ ] Run full suite and commit.

### Task 6: Harden orchestrator contracts

**Files:**
- Modify orchestrator models/parser/router/catalog/service/config
- Add security-focused tests

- [ ] Test finite confidence bounds.
- [ ] Test plain, fenced, and surrounded JSON.
- [ ] Reject conflicting multiple objects.
- [ ] Reject unknown, whitespace-tricked, and Unicode-confusable actions.
- [ ] Enforce response-size limits.
- [ ] Enforce loopback-only HTTP and external-redirect rejection.
- [ ] Test broker error classification and keyword fallback.
- [ ] Test approvals, replay, parameter mutation, and audit redaction.
- [ ] Run full suite and commit.

### Task 7: Create Android broker protocol and project

**Files:**
- Create complete `android-broker/` Gradle project
- Create protocol DTOs and unit tests

- [ ] Verify current official LiteRT-LM Maven version and Kotlin signatures.
- [ ] Pin concrete versions.
- [ ] Create Android project and protocol/error DTOs.
- [ ] Implement loopback-only server configuration.
- [ ] Implement bearer authentication and request limits.
- [ ] Add unit tests and commit.

### Task 8: Implement secure model lifecycle

**Files:**
- Android model registry/import/token/engine modules and tests

- [ ] Implement Keystore-backed token protection.
- [ ] Implement SAF model selection and atomic import.
- [ ] Validate `.litertlm`, size, normalized name, and SHA-256.
- [ ] Implement model load/unload and serialized inference coordinator.
- [ ] Close old engines before replacement.
- [ ] Add timeout, queue, and lifecycle tests.
- [ ] Commit.

### Task 9: Implement foreground service and UI

**Files:**
- Android service, notification, manifest, activities/screens, tests

- [ ] Start only from visible user interaction.
- [ ] Declare the verified foreground-service type and permissions.
- [ ] Prevent duplicate servers.
- [ ] Add start/stop, import, load/unload, backend, token, config-copy, and diagnostics UI.
- [ ] Keep token hidden by default.
- [ ] Run Android unit tests/lint/build and commit.

### Task 10: Security review and remediation

- [ ] Write/update threat model.
- [ ] Run Codex Security repository and diff scans.
- [ ] Validate candidates.
- [ ] Analyze attack paths for reportable findings.
- [ ] Fix all validated high/critical and feasible medium issues.
- [ ] Rerun checks and commit.

### Task 11: Android emulator QA

- [ ] Build APK.
- [ ] Install and launch through ADB.
- [ ] Use UI tree for interactions.
- [ ] Verify foreground notification and server lifecycle.
- [ ] Test health, invalid token, valid token, stop, rotation, and process recreation.
- [ ] Capture screenshots, UI trees, commands, and logcat.
- [ ] Record hardware-only Galaxy A33 gaps.

### Task 12: CI, packaging, and integration

- [ ] Add Python, Android, security, and release workflows with least permissions.
- [ ] Pin third-party actions to full commit SHAs.
- [ ] Create full, upgrade, source, APK, manifest, and checksum artifacts.
- [ ] Test clean install and upgrade.
- [ ] Run CodeRabbit review and address validated feedback.
- [ ] Run verification-before-completion.
- [ ] Merge locally to `main`.
- [ ] Push private repository.
- [ ] Inspect workflow runs.
- [ ] Remove worktree/feature branch and report evidence.
