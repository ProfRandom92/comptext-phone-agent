# CompText Phone Agent

CompText Phone Agent is a local-first, non-root Android storage, file, backup and device assistant designed for **Termux on ARM64**, with the Samsung Galaxy A33 as the primary target. Read-only analysis is the default. Every mutation is represented as a typed plan, checked against hard exclusions, bound to an expiring approval token and written to a SQLite audit trail.

## Security model

- Default mode: `analysis`; it cannot move, rename, delete, overwrite or upload.
- Organize mode: reversible local changes, primarily the internal trash, after approval.
- Controlled mode: uploads, large batches, permanent deletion and overwrite after plan-bound approval.
- Risk 0: read only. Risk 1: reversible local change. Risk 2: upload/batch. Risk 3: irreversible.
- Approval tokens are HMAC-signed, installation/user/session/action/path/count/size/plan-hash/time/risk bound, expiring and single-use.
- Paths containing `comptext` under a scanned storage root are analyze-only and never delete/upload by default.
- `.ssh`, `.env`, Git metadata, virtual environments, Android, Samsung, WhatsApp, DCIM and Pictures receive conservative protection.
- No arbitrary `eval`, shell tool or language-model-generated shell execution exists.
- Subprocesses use argument arrays, timeouts and `shell=False`.
- Android access time is not trusted. Age recommendations use `mtime`.

## Termux prerequisites

Install Termux and Termux:API from the same compatible source, preferably F-Droid or the official GitHub releases. Do not mix an obsolete Play Store Termux build with a current Termux:API build.

In Termux, first run:

```bash
termux-setup-storage
```

Confirm Android's storage permission prompt. This creates `~/storage/shared`. Android Scoped Storage still restricts locations such as parts of `Android/data`; the agent reports such errors and does not try to bypass them.

Samsung may stop long scans in the background. Exempt Termux from battery optimization while running deliberate long operations, then restore the stricter setting when not needed.

## Installation

```bash
git clone <repository-url> comptext-phone-agent
cd comptext-phone-agent
bash install-termux.sh
export PATH="$HOME/.local/bin:$PATH"
comptext-phone doctor
```

The installer checks Python 3.12+, creates `.venv`, installs the project, preserves existing configuration, creates data/report/token directories and installs `~/.local/bin/comptext-phone`. It does not execute remote pipe-to-shell installers.

Fish:

```fish
fish_add_path $HOME/.local/bin
comptext-phone doctor
# or directly:
./start.fish doctor
```

Sandbox verification:

```bash
bash install-termux.sh --sandbox
./.venv/bin/comptext-phone demo --path ./mock-phone
pytest
```

## First analysis

```bash
comptext-phone scan --path ~/storage/shared --top 30
comptext-phone analyze large --path ~/storage/shared
comptext-phone analyze old --path ~/storage/shared
comptext-phone analyze types --path ~/storage/shared
comptext-phone duplicates --path ~/storage/shared --verify
```

The duplicate process groups by size, computes a first/last partial hash, then performs SHA-256 verification. It never deletes duplicates.

## Cleanup approval flow

```bash
comptext-phone cleanup plan --path ~/storage/shared --old-days 365 --json
comptext-phone cleanup approve <PLAN_ID> --phrase APPROVE
comptext-phone cleanup apply <PLAN_ID>
comptext-phone trash list
comptext-phone trash restore <ITEM_ID> --phrase APPROVE
```

Cleanup candidates are conservative: old, unprotected APK/archive/temp/cache files. They are moved to `.CompTextTrash`; direct deletion is not the default.

Permanent purge is risk 3:

```bash
comptext-phone trash purge
# review the generated plan, then use the exact phrase:
comptext-phone trash purge --phrase "DELETE PERMANENTLY"
```

`--yes` is intentionally not implemented as a risk-3 bypass.

## Reports

```bash
comptext-phone report --path ~/storage/shared --format markdown
comptext-phone report --path ~/storage/shared --format json
comptext-phone report --path ~/storage/shared --format html
```

HTML is self-contained and uses no external CDN. Reports include scan metadata, largest files/directories, types, old files, duplicates, protected paths, errors and recommendations.

## Termux:API

Read operations:

```bash
comptext-phone device battery
comptext-phone device wifi
comptext-phone device volume
comptext-phone device clipboard-get
comptext-phone device clipboard-set "text"
comptext-phone device tts "text"
comptext-phone device vibrate --duration-ms 250
```

Optional write operations:

```bash
comptext-phone device notify --title "CompText" --content "Scan complete"
```

All wrappers use explicit command arrays, short timeouts, clear errors and a complete mock client:

```bash
comptext-phone device battery --mock
```

Clipboard reading is available only in the internal client for an explicit future UI action; it is not performed during scans or status checks and clipboard contents are redacted from audit data.

## rclone backup

Configure `rclone` manually; the agent never prints `rclone.conf` or secrets.

Google Drive:

```bash
pkg install rclone
rclone config
comptext-phone backup plan --path ~/storage/shared/Download/archive.zip --destination gdrive:PhoneBackup
comptext-phone backup approve <PLAN_ID> --phrase APPROVE
comptext-phone backup apply <PLAN_ID> --dry-run
```

Nextcloud WebDAV is configured as an rclone WebDAV remote, then used similarly:

```bash
comptext-phone backup plan --path ~/storage/shared/Documents/file.pdf --destination nextcloud:PhoneBackup
comptext-phone backup approve <PLAN_ID> --phrase APPROVE
comptext-phone backup apply <PLAN_ID> --dry-run
```

An external upload requires controlled mode plus a valid approval token when `--execute` is selected. Local files are never deleted after upload.

## Local dashboard

```bash
comptext-phone serve
```

It binds only to `127.0.0.1` by configuration validation. A random in-memory session token is required for API routes. State-changing operations use POST and remain subject to the same approval engine. The initial v0.1 dashboard is intentionally small and read-oriented.

## Tests

```bash
pytest
```

Coverage includes configuration, exclusions, path traversal, symlink escape, scans, size/type/age analysis, duplicate verification, approval expiry/change/reuse, redaction, trash/restore/collision, backup dry-run, Termux:API failures/mocks and CLI smoke/JSON behavior.

## Update and uninstall

```bash
bash update.sh
bash uninstall.sh
```

Uninstall preserves configuration, approvals, audit logs and trash metadata by default. Full removal requires:

```bash
bash uninstall.sh --purge-data
```

and the exact interactive phrase `DELETE COMPTEXT DATA`.

## Known Android limits

- No root and no bypass of Scoped Storage.
- Some `Android/data` paths remain inaccessible.
- File `atime` can be disabled, stale or misleading; `mtime` is used.
- Long background scans can be stopped by Samsung/Android power management.
- Termux and Termux:API must come from compatible release channels.
- The first version does not perform unrestricted screen control or arbitrary shell execution.
- rclone remote setup remains a deliberate user action because it handles secrets.

See `docs/` for architecture, permissions, security, command reference and troubleshooting.


## Termux dependency portability

Pydantic is pinned to the universal pure-Python 1.10.24 wheel, so Termux does not need a Rust toolchain for configuration validation. FastAPI is capped below 0.126 because that range still supports Pydantic v1.

## LLM providers

The tool-enabled interactive chat uses the native Ollama Cloud `/api/chat` schema. Its
provider, model, and base URL are explicit and can be inspected without exposing keys:

```bash
comptext-phone provider-doctor --json
comptext-phone chat --provider ollama-cloud --model gpt-oss:20b
```

Typed planner adapters also exist for OpenAI, OpenRouter, Gemini, NVIDIA NIM, local
OpenAI-compatible servers, and deterministic tests. Their output is restricted to
`scan`, `duplicates`, or `cleanup_plan`; it cannot emit or execute shell commands.
Selecting one of those adapters for the tool-chat command is rejected explicitly until
that provider implements the tool-call runtime contract. The local keyword orchestrator
does not require a cloud provider or API key.

## Version 0.2 chat upgrade

The Termux chat now uses native Ollama `/api/chat` tool calls through a lightweight
`httpx` adapter. The official `ollama-python` package is intentionally not a mandatory
Termux dependency because current releases require Pydantic 2 and `pydantic-core`.
That dependency chain is not reliable on Android Python 3.14.

Included improvements:

- native structured tool calls with a fixed local allowlist;
- `prompt_toolkit` history, completion and slash commands;
- Rich Markdown and streamed final answers;
- SQLite chat sessions and automatic resume of the latest session;
- `/new` and `/clear` session controls;
- SQLite partial/SHA-256 cache keyed by path, size and `mtime_ns`;
- cache invalidation after file changes;
- cleanup requests create plans only and never apply them from chat.

Start or resume the latest chat:

```bash
comptext-phone chat
```

Create a fresh conversation:

```bash
comptext-phone chat --new
```

## 0.3 Agent Runtime and mobile TUI

```bash
comptext-phone tui
comptext-phone chat --simple
comptext-phone tui --safe-mode
```

Version 0.3 adds a bounded multi-step loop, durable hash-chained runtime events, context compaction, local artifacts, and a responsive Textual interface. No free shell or autonomous file mutation is introduced.


## Neon TUI 0.4

Start with `comptext-phone tui`. The interface adapts at 60 and 90 terminal columns: compact phone layout, wide mobile layout, and desktop layout with a persistent status sidebar. `Ctrl+P` opens the status drawer on phones, `Ctrl+N` creates a session, `Ctrl+C` signals cancellation, and `Ctrl+Q` exits. Runtime events are projected through a fixed trusted component catalog; the model cannot generate widgets. Durable local signals and idempotency keys provide Temporal-style restart safety without running a Temporal server on Android.


## Live Agent Console

Version 0.5 renders durable runtime events while the agent is working. Tool cards are updated in place by call ID, Ctrl+P opens the mobile command palette, Ctrl+S opens system status, and `comptext-phone tui-doctor` reports terminal/layout readiness.


## Local two-model orchestrator

CompText 0.6 adds a local orchestrator for Android. A small FunctionGemma-style router can map simple German commands to a fixed trusted action catalog, while complex requests remain with the planner model. Router output is always schema-validated and checked by the existing RuntimePolicy before any handler runs.

Preview a route without executing it:

```bash
comptext-phone orchestrator route "Prüfe meinen Akku" --json
```

Execute an allowed action explicitly:

```bash
comptext-phone orchestrator route "Prüfe meinen Akku" --execute --json
```

Inspect the orchestrator:

```bash
comptext-phone orchestrator doctor --json
```

The default `keyword` router is fully local and requires no model server. For
MobileActions-270M, set `COMPTEXT_BROKER_TOKEN` and configure `router_mode: broker` or
`auto` with the authenticated loopback Android broker. The client uses only the fixed
`/v1/route` endpoint, never follows redirects, and never falls back to a cloud host.
Remote broker hosts, arbitrary shell commands, and raw Android intents are rejected.
