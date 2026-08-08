# Portable Starlette Dashboard Implementation Plan

> **For agentic workers:** Use systematic debugging and TDD for any follow-up failure. This plan records the implementation path including the rejected Pydantic 2 experiment so later work does not repeat it.

**Goal:** Restore the authenticated loopback dashboard on a maintained web stack while keeping the native Termux installation free of mandatory Rust/native-extension dependencies.

**Final architecture:** Keep `pydantic==1.10.25` in the core. Use `starlette==1.5.0` + `uvicorn==0.51.0` only in the optional `dashboard` extra. Use `httpx2==2.7.0` only for dashboard TestClient coverage.

## Global constraints

- Dashboard host remains restricted to `127.0.0.1`, `localhost`, or `::1`.
- No dashboard endpoint executes cleanup, delete, move, upload, arbitrary shell, or raw Android intents.
- Existing token, CSRF, storage-root, approval, redaction, and audit controls are not weakened.
- Dashboard dependencies remain optional.
- Base CLI/TUI installation keeps working without dashboard packages.
- No automatic merge into `docs/community-release-0.6.1` or `main`.

## Completed TDD history

- [x] Added mandatory dashboard integration tests before restoring dependencies.
- [x] Added a `serve` regression that requires Uvicorn to receive loopback host/port, `reload=False`, and `access_log=False`.
- [x] Confirmed RED in GitHub CI: the test collection failed specifically because the dashboard dependency was absent.
- [x] Tested a Pydantic 2 + FastAPI implementation on Linux CI.
- [x] Confirmed the modern FastAPI stack passed dependency audit and functionally ran all dashboard tests.
- [x] Rejected that architecture after Termux portability research showed Pydantic 2 would introduce a `pydantic-core` native/Rust dependency into the primary Android installation path.
- [x] Pivoted to direct Starlette + Uvicorn while keeping Pydantic 1.10.25.

### Task 1: Portable dependency contract

**Files:** `pyproject.toml`, `requirements-termux.txt`, `tests/unit/test_release_metadata.py`

- [x] Keep core `pydantic==1.10.25`.
- [x] Set dashboard extra to `starlette==1.5.0`, `uvicorn==0.51.0`.
- [x] Add test-only `httpx2==2.7.0` for maintained Starlette TestClient behavior.
- [x] Assert the dashboard extra contains neither FastAPI nor `pydantic-core`.
- [x] Align `requirements-termux.txt` with the portable core pin.

### Task 2: Starlette application migration

**Files:** `src/comptext_phone_agent/api/app.py`, `src/comptext_phone_agent/api/routes.py`

- [x] Replace FastAPI application with `Starlette(debug=False, routes=routes)`.
- [x] Preserve generated in-memory session and CSRF tokens.
- [x] Replace dependency-injection guards with explicit Starlette request guards.
- [x] Use `secrets.compare_digest` for token comparisons.
- [x] Preserve storage-root containment.
- [x] Preserve existing read endpoints and POST-only scan behavior.
- [x] Validate scan JSON through the existing Pydantic request schema and return 422 for invalid payloads.
- [x] Keep the HTML self-contained with no external CDN.

### Task 3: Restore CLI startup

**File:** `src/comptext_phone_agent/cli.py`

- [x] Lazy-import Uvicorn and the dashboard app.
- [x] Exit 5 with an explicit `.[dashboard]` install instruction when optional dependencies are missing.
- [x] Create the app from the normal application context.
- [x] Print loopback URL and generated session token to stderr.
- [x] Run Uvicorn with `reload=False`, `access_log=False`.

### Task 4: CI and audit coverage

**Files:** `.github/workflows/python-ci.yml`, `.github/workflows/security-ci.yml`

- [x] Python CI installs `.[test,tui,dashboard]` so dashboard tests cannot silently skip.
- [x] Security CI installs `.[test,dashboard]` so the optional web stack is included in `pip-audit`.
- [ ] Run final Python 3.12 and 3.13 CI on the completed Starlette implementation.
- [ ] Run final Security CI and verify dependency audit + Bandit.
- [ ] Inspect logs for deprecations and unexpected optional dependencies.

### Task 5: Documentation and review

**Files:** `README.md`, `docs/architecture.md`, `docs/termux-setup.md`, `docs/troubleshooting.md`, this spec/plan

- [x] Document why Pydantic 2 was rejected for the Termux core.
- [x] Document Starlette/Uvicorn dashboard installation and security boundaries.
- [ ] Add concise dashboard usage to README.
- [ ] Search active branch files for stale statements that `serve` is intentionally disabled.
- [ ] Perform an independent skeptical diff review / CodeRabbit review when available.
- [ ] Resolve all validated critical or important findings.
- [ ] Update PR #5 title/body from the obsolete Pydantic 2 wording to the portable Starlette design.
- [ ] Mark PR #5 ready for review only after fresh final CI is green.

### Task 6: Handoff to next optimization PR

Do **not** mix the following into this PR:

- Python 3.14 CI matrix expansion;
- SBOM generation;
- GitHub artifact attestations / provenance;
- repository branch-protection/security setting changes.

Those are the next stacked optimization after PR #5 is independently verified.
