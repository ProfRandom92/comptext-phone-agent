# Architecture

## Runtime boundaries

CompText Phone Agent is a Python 3.12+ application designed for Termux on Android without root, Docker, systemd, Node.js, or mandatory Rust tooling. The CLI is the primary interface. An optional authenticated dashboard can be installed through the `dashboard` extra and is restricted to loopback hosts by validated configuration.

The runtime is divided into six boundaries:

1. **Read boundary** — scanners, analyzers, duplicate detection, reports, and read-only Termux:API calls.
2. **Planning boundary** — converts explicit CLI or natural-language requests into typed `ActionPlan` objects.
3. **Policy boundary** — evaluates mode, risk class, path normalization, symlink containment, exclusions, and immutable CompText protection.
4. **Approval boundary** — creates HMAC-signed, expiring, single-use tokens bound to the exact plan hash and installation.
5. **Execution boundary** — accepts only known typed actions; no arbitrary shell/eval interface exists.
6. **Audit boundary** — stores redacted events, plans, approvals, and trash metadata in SQLite transactions.

## Package map

- `storage/`: streaming scan, classification, aggregation, duplicate pipeline, cleanup planning, trash, and restore.
- `approvals/`: risk policy, token encoding, plan persistence, expiry, mutation, and replay checks.
- `audit/`: WAL-mode SQLite database, event logger, and recursive secret redaction.
- `backup/`: destination parsing, approved plans, local atomic copy, SHA-256 verification, and rclone wrapper.
- `termux_api/`: bounded subprocess client and deterministic mock client.
- `agent/`: deterministic planner, strict tool schemas, optional provider adapters, and execution policy.
- `reports/`: local-only Markdown, JSON, and standalone HTML output.
- `api/`: Starlette-based loopback dashboard with in-memory session token, CSRF enforcement, and storage-root containment.
- `mocks/`: realistic phone filesystem and device responses for offline tests.

## Data flow

`request -> validated path/tool input -> scan or action plan -> policy/exclusions -> approval -> executor -> audit`

Read-only work stops before approval. Any modifying operation must be represented by an immutable plan. The executor validates every action before consuming the approval token, then executes only supported operations.

## Persistent data

By default, runtime state is under `~/.comptext-phone-agent/`:

- `state.sqlite3`: audit events, approvals, plans, and trash metadata.
- `approval.key`: local HMAC key, mode `0600`.
- `tokens/`: approved token files, mode `0600`.
- `reports/`: generated reports.
- `install.log`: installer record.

The user configuration is stored separately at `~/.config/comptext-phone-agent/config.yaml` and is preserved during normal uninstall.

The dashboard session and CSRF tokens are generated in memory when the dashboard starts. The dashboard layer does not persist either token.

## Android assumptions

The application treats `mtime` as the age signal because Android access times may be disabled, cached, or updated inconsistently. It does not assume access to `/Android/data`, does not follow symlinks by default, and never assumes root or a desktop Linux filesystem.

## Dependency portability

The Termux core deliberately stays on `pydantic==1.10.25`. That line is pure Python and avoids making the Android installation depend on the Rust-based `pydantic-core` build path required by Pydantic 2. This matters because the primary deployment target is native Termux rather than a conventional manylinux environment.

The optional dashboard is therefore built directly on `starlette==1.5.0` and `uvicorn==0.51.0` instead of using FastAPI. This keeps the web layer modern and audited without forcing Pydantic 2 into the Termux runtime.

Python CI installs the dashboard extra so its token, CSRF, storage-root, HTTP-method, and read-view integration tests cannot silently skip. Security CI installs and audits the same optional stack with `pip-audit`. The base CLI/TUI installation does not require a web server.
