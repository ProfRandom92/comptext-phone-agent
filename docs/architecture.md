# Architecture

## Runtime boundaries

CompText Phone Agent is a Python 3.12+ application designed for Termux on Android without root, Docker, systemd, Node.js, or mandatory Rust tooling. The CLI is the primary interface. Dashboard source is retained for a future web-stack migration, but the `serve` command fails closed in 0.6.1.

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
- `api/`: loopback dashboard with in-memory session token and CSRF enforcement.
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

## Android assumptions

The application treats `mtime` as the age signal because Android access times may be disabled, cached, or updated inconsistently. It does not assume access to `/Android/data`, does not follow symlinks by default, and never assumes root or a desktop Linux filesystem.

## Dependency portability

Pydantic is pinned to the universal pure-Python 1.10.25 release, which adds minimal Python 3.14 support without requiring `pydantic-core`. Dashboard dependencies are intentionally not shipped in 0.6.1; current FastAPI releases require Pydantic 2, so re-enabling the web interface is treated as a separate migration rather than reviving the legacy dependency line.
