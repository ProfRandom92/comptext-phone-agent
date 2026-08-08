# Pydantic 2 Dashboard Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate CompText Phone Agent to native Pydantic 2 semantics and re-enable its loopback-only FastAPI dashboard as an explicit optional extra.

**Architecture:** Keep the existing application/API boundaries. Replace the Pydantic compatibility shim with native v2 APIs, migrate the only legacy planner parse call, and restore `serve` through lazy optional imports. Dashboard dependencies stay outside the base install, and all current security invariants remain unchanged.

**Tech Stack:** Python 3.12+, Pydantic 2.13.4, FastAPI 0.139.2, Uvicorn 0.51.0, Typer, pytest.

## Global Constraints

- Dashboard host must remain restricted to `127.0.0.1`, `localhost`, or `::1`.
- No dashboard endpoint may execute cleanup, delete, move, upload, arbitrary shell, or raw Android intent operations.
- Existing token, CSRF, storage-root, approval, redaction, and audit controls must not be weakened.
- FastAPI and Uvicorn must remain optional through the `dashboard` extra.
- Base CLI/TUI installation must continue to work without dashboard dependencies.
- No changes are merged into `main` or the 0.6.1 release branch automatically.

---

### Task 1: Lock regression expectations

**Files:**
- Modify: `tests/unit/test_config.py`
- Modify: `tests/integration/test_dashboard.py`
- Modify: `tests/test_cli_smoke.py`
- Test: the same three files

**Interfaces:**
- Consumes: existing `AppConfig`, `create_app`, Typer `app`.
- Produces: failing tests that define native Pydantic 2 and restored `serve` behavior.

- [ ] **Step 1: Add a native-Pydantic-2 configuration assertion**

Add a test that asserts `AppConfig.model_config["extra"] == "forbid"` and that an invalid dashboard host still raises `ValidationError`.

- [ ] **Step 2: Remove the dashboard import skip**

Replace the `pytest.importorskip("fastapi", ...)` gate with direct imports so a dashboard-enabled CI install must execute the five existing security integration tests.

- [ ] **Step 3: Replace the fail-closed serve test**

Patch `uvicorn.run`, invoke `comptext-phone serve`, and assert the call receives the configured host/port, `reload=False`, and an app whose state has a non-empty session token.

- [ ] **Step 4: Run these tests before production changes**

Expected result: failures because the branch still pins Pydantic 1, the dashboard extra is empty, and `serve` exits with code 5.

- [ ] **Step 5: Commit the failing regressions**

Commit message: `test: define supported dashboard migration contract`.

### Task 2: Migrate models and dependencies

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/comptext_phone_agent/config.py`
- Modify: `src/comptext_phone_agent/agent/provider_planner.py`
- Test: `tests/unit/test_config.py` and planner/orchestrator tests

**Interfaces:**
- Consumes: Pydantic `BaseModel`, `ConfigDict`, `Field`, `field_validator`.
- Produces: native v2 `CompatModel` and v2 validation calls.

- [ ] **Step 1: Update dependency pins**

Set base `pydantic==2.13.4` and `dashboard = ["fastapi==0.139.2", "uvicorn==0.51.0"]`.

- [ ] **Step 2: Replace compatibility shim**

Use:

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator

class CompatModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
```

Remove the custom `model_validate` and `model_dump` methods.

- [ ] **Step 3: Migrate validators**

Replace each `@validator(...)` with `@field_validator(...)` while preserving current return values and error messages.

- [ ] **Step 4: Migrate provider planner parsing**

Replace `Intent.parse_obj(json.loads(raw))` with `Intent.model_validate(json.loads(raw))`.

- [ ] **Step 5: Run focused config/planner tests**

Expected result: all focused tests pass under Pydantic 2.

- [ ] **Step 6: Commit**

Commit message: `feat: migrate core models to Pydantic 2`.

### Task 3: Restore the dashboard command

**Files:**
- Modify: `src/comptext_phone_agent/cli.py`
- Test: `tests/test_cli_smoke.py`
- Test: `tests/integration/test_dashboard.py`

**Interfaces:**
- Consumes: `get_context()`, `create_app(context)`, `uvicorn.run(...)`.
- Produces: working `comptext-phone serve` command.

- [ ] **Step 1: Implement lazy optional imports**

Inside `serve()`, import `uvicorn` and `.api.app.create_app`. If unavailable, print a plain install instruction for `pip install -e '.[dashboard]'` and exit 5.

- [ ] **Step 2: Build the app from the normal context**

Create `ctx = get_context()` and `dashboard = create_app(ctx)`.

- [ ] **Step 3: Print local access information**

Write the loopback URL and generated session token to stderr. Do not write credentials to files or audit logs.

- [ ] **Step 4: Start Uvicorn safely**

Call:

```python
uvicorn.run(
    dashboard,
    host=ctx.config.dashboard.host,
    port=ctx.config.dashboard.port,
    reload=False,
    access_log=False,
)
```

- [ ] **Step 5: Run serve and dashboard integration tests**

Expected result: restored command test and all existing dashboard token/CSRF/path/HTTP-method tests pass.

- [ ] **Step 6: Commit**

Commit message: `feat: restore loopback dashboard on supported stack`.

### Task 4: CI and documentation validation for this PR

**Files:**
- Modify only if required by verified failures: README/dashboard docs.
- Do not add Python 3.14 or supply-chain attestation here; those belong to the next stacked PR.

**Interfaces:**
- Consumes: the complete feature branch.
- Produces: a reviewable PR with evidence.

- [ ] **Step 1: Run full Python CI with `.[test,tui,dashboard]` for this branch**

The feature branch CI must install the dashboard extra so integration tests cannot silently skip.

- [ ] **Step 2: Run dependency/security gates**

Require `pip check`, `pip-audit`, Bandit, workflow-pin guard, tracked-file guard, compileall, and installation verification.

- [ ] **Step 3: Inspect the final diff**

Confirm there are no non-loopback host changes, new mutation endpoints, approval bypasses, or secret persistence.

- [ ] **Step 4: Open a stacked PR**

Base: `docs/community-release-0.6.1`.

Title: `feat: migrate to Pydantic 2 and restore local dashboard`.

- [ ] **Step 5: Independent review**

Run CodeRabbit when available; otherwise record that the connector was unavailable and perform a second skeptical diff review. Resolve all validated critical/important findings before considering the PR ready.
