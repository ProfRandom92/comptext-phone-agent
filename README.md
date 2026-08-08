# CompText Phone Agent

<p align="center">
  <strong>Local-first Android storage analysis and controlled cleanup for Termux.</strong><br>
  Read-only by default. Typed plans, explicit approval, reversible actions and durable audit evidence.
</p>

<p align="center">
  <a href="https://github.com/ProfRandom92/comptext-phone-agent/actions/workflows/python-ci.yml"><img alt="Python CI" src="https://github.com/ProfRandom92/comptext-phone-agent/actions/workflows/python-ci.yml/badge.svg"></a>
  <a href="https://github.com/ProfRandom92/comptext-phone-agent/actions/workflows/android-ci.yml"><img alt="Android CI" src="https://github.com/ProfRandom92/comptext-phone-agent/actions/workflows/android-ci.yml/badge.svg"></a>
  <a href="https://github.com/ProfRandom92/comptext-phone-agent/actions/workflows/security-ci.yml"><img alt="Security CI" src="https://github.com/ProfRandom92/comptext-phone-agent/actions/workflows/security-ci.yml/badge.svg"></a>
  <img alt="Python 3.12+" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white">
  <img alt="Android via Termux" src="https://img.shields.io/badge/Android-Termux-111827?logo=android&logoColor=3DDC84">
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-22c55e.svg"></a>
  <img alt="Release maturity" src="https://img.shields.io/badge/Release-0.6.1%20candidate-22d3ee">
</p>

> **Project status:** Version `0.6.1` is being prepared as a community release. The repository is suitable for review and sandbox testing; release publication remains a separate explicit step.

[Quick start](#quick-start) · [Safety model](#safety-model) · [Architecture](#architecture) · [Release notes](docs/release/0.6.1-release-notes.md) · [Security](SECURITY.md)

## Why CompText Phone Agent?

Android storage tools often jump directly from “find” to “delete.” CompText Phone Agent separates evidence, planning, approval and execution. It is designed for privacy-conscious users who want useful automation without granting a model unrestricted shell access or silent destructive authority.

The primary target is **Termux on ARM64 Android**, with the Samsung Galaxy A33 used as a reference device. No root access is required or attempted.

## Core capabilities

- storage scans with largest-file and directory summaries;
- old-file, file-type and duplicate analysis;
- SHA-256 duplicate verification;
- Markdown, JSON and self-contained HTML reports;
- reversible cleanup through an internal trash area;
- plan-bound approvals for mutating actions;
- optional rclone backup planning and execution;
- Termux:API device adapters with deterministic mocks;
- local Textual TUI, chat runtime and bounded orchestration;
- optional authenticated Starlette dashboard on loopback only;
- optional authenticated loopback Android LiteRT-LM broker;
- SQLite audit, approvals, cache and chat/session state.

## Safety model

CompText Phone Agent treats mutation as a controlled protocol rather than a convenience flag.

| Risk | Meaning | Default behavior |
|---|---|---|
| 0 | Read-only inspection | Allowed |
| 1 | Reversible local change | Plan and approval required |
| 2 | Upload or large batch | Controlled mode and approval required |
| 3 | Irreversible action | Explicit destructive phrase and policy checks |

The execution path is:

**Analyze → Plan → Approve → Apply → Audit**

Approval tokens are HMAC-signed, expiring, single-use and bound to the installation, user, session, action, paths, item count, size, plan hash, time window and risk level. Protected paths are rechecked when a plan is applied.

Important boundaries:

- analysis mode cannot move, rename, delete, overwrite or upload;
- cleanup requests from chat create plans only;
- arbitrary model-generated shell execution is not supported;
- subprocesses use argument arrays, timeouts and `shell=False`;
- paths containing `comptext` under a scanned storage root are analyze-only by default;
- `.ssh`, `.env`, Git metadata, virtual environments and sensitive Android/media paths receive conservative protection;
- Android access time is not trusted; age recommendations use modification time.

## Quick start

### Requirements

- Android with a current Termux build;
- Termux and Termux:API from compatible sources, preferably F-Droid or their official GitHub releases;
- Python `3.12+`;
- storage permission granted through `termux-setup-storage`.

Do not mix the obsolete Play Store Termux build with a current Termux:API package.

### Install from source

```bash
pkg update
pkg install git python
git clone https://github.com/ProfRandom92/comptext-phone-agent.git
cd comptext-phone-agent
bash install-termux.sh
export PATH="$HOME/.local/bin:$PATH"
comptext-phone doctor
```

Fish users can add the binary directory permanently:

```fish
fish_add_path $HOME/.local/bin
comptext-phone doctor
```

### Safe sandbox verification

The first test does not require real phone storage:

```bash
bash install-termux.sh --sandbox
./.venv/bin/comptext-phone demo --path ./mock-phone
./.venv/bin/pytest
```

See the complete [first-user smoke test](docs/release/0.6.1-smoke-test.md).

## Common workflows

### Analyze storage

```bash
comptext-phone scan --path ~/storage/shared --top 30
comptext-phone analyze large --path ~/storage/shared
comptext-phone analyze old --path ~/storage/shared
comptext-phone analyze types --path ~/storage/shared
comptext-phone duplicates --path ~/storage/shared --verify
```

Duplicate detection groups by size, compares partial hashes and then performs full SHA-256 verification. It never deletes duplicates automatically.

### Create and apply a reversible cleanup plan

```bash
comptext-phone cleanup plan --path ~/storage/shared --old-days 365 --json
comptext-phone cleanup approve <PLAN_ID> --phrase APPROVE
comptext-phone cleanup apply <PLAN_ID>
comptext-phone trash list
comptext-phone trash restore <ITEM_ID> --phrase APPROVE
```

Cleanup candidates are limited to conservative categories such as old APK, archive, temporary and cache files. The default operation moves them to `.CompTextTrash`.

Permanent purge is risk 3 and requires the exact destructive phrase:

```bash
comptext-phone trash purge --phrase "DELETE PERMANENTLY"
```

There is deliberately no `--yes` bypass for risk-3 actions.

### Generate reports

```bash
comptext-phone report --path ~/storage/shared --format markdown
comptext-phone report --path ~/storage/shared --format json
comptext-phone report --path ~/storage/shared --format html
```

HTML output is self-contained and uses no external CDN.

### Inspect device adapters

```bash
comptext-phone device battery
comptext-phone device wifi
comptext-phone device volume
comptext-phone device battery --mock
```

Mocks allow development and verification without relying on Android hardware state.

### Plan an rclone backup

```bash
pkg install rclone
rclone config
comptext-phone backup plan \
  --path ~/storage/shared/Download/archive.zip \
  --destination gdrive:PhoneBackup
comptext-phone backup approve <PLAN_ID> --phrase APPROVE
comptext-phone backup apply <PLAN_ID> --dry-run
```

The agent does not configure or print `rclone.conf`, and local files are not deleted after upload.

## Local agent interfaces

```bash
comptext-phone tui
comptext-phone chat
comptext-phone chat --new
comptext-phone chat --simple
comptext-phone tui --safe-mode
comptext-phone tui-doctor
```

The runtime uses a fixed trusted tool catalog, bounded multi-step execution, durable hash-chained events and context compaction. Model output cannot generate arbitrary UI widgets or execute unrestricted shell commands.

The local two-model orchestrator can preview or execute a validated route:

```bash
comptext-phone orchestrator route "Prüfe meinen Akku" --json
comptext-phone orchestrator route "Prüfe meinen Akku" --execute --json
comptext-phone orchestrator doctor --json
```

The default keyword router is local. Optional broker mode communicates only with the authenticated loopback Android broker endpoint and rejects remote broker hosts, raw Android intents and arbitrary commands.

### Optional local dashboard

The dashboard is not installed by the default Termux setup. Add it explicitly from the repository directory:

```bash
./.venv/bin/python -m pip install -e '.[dashboard]'
comptext-phone serve
```

`serve` starts a Starlette application through Uvicorn and prints the local URL plus a generated session token to stderr. Dashboard hosts are restricted to `127.0.0.1`, `localhost`, or `::1` by configuration validation.

Protected GET views require `X-CompText-Token`; POST scan requests additionally require `X-CompText-CSRF`. Requested storage paths remain constrained to configured roots, the HTML uses no external CDN, and the dashboard exposes no unrestricted cleanup, delete, upload, shell, or raw Android-intent endpoint.

The web layer intentionally uses Starlette directly rather than FastAPI so the primary Termux runtime can stay on the pure-Python Pydantic 1 line instead of requiring Rust-based `pydantic-core`.

## Architecture

```text
CLI / Textual TUI / local chat / optional loopback dashboard
                │
                ▼
Tool registry / typed planner / bounded runtime
                │
                ▼
Runtime policy ─ approval engine ─ audit chain
                │
     ┌──────────┼───────────┬───────────┐
     ▼          ▼           ▼           ▼
Storage     Duplicates    Reports     Backup/device adapters
     │          │           │           │
     └──────────┴──────┬────┴───────────┘
                       ▼
 SQLite: audit, approvals, cache, sessions
                       │
             optional loopback broker
```

Optional LLM providers remain behind typed planner adapters. Their output is restricted to supported actions and cannot directly invoke a shell.

Detailed design material is available under [`docs/`](docs/).

## Supported environment and Android limits

- no root and no scoped-storage bypass;
- some `Android/data` locations remain inaccessible;
- file access time may be disabled, stale or misleading;
- Android or Samsung power management can stop long background scans;
- rclone remote setup remains a deliberate user action because it handles secrets;
- unrestricted screen control is outside the current scope;
- the Android broker and dashboard are optional and loopback-only.

## Verification

Run the Python suite:

```bash
pytest
```

The repository includes dedicated GitHub Actions workflows for Python CI, Android CI, security checks and release packaging. Coverage includes exclusions, path traversal, symlink escape, duplicate verification, approval expiry/change/reuse, redaction, reversible trash behavior, backup dry-run, Termux:API failures and mocks, CLI behavior, dashboard token/CSRF/storage-root/HTTP-method boundaries, release metadata and workflow security.

Python CI installs the optional dashboard stack so its integration tests cannot silently skip. Security CI audits the same optional dependencies with `pip-audit`.

Release evidence and remaining gates are recorded in [`docs/release/0.6.1-evidence.md`](docs/release/0.6.1-evidence.md) and [`docs/release/0.6.1-checklist.md`](docs/release/0.6.1-checklist.md).

## Project status and roadmap

Version `0.6.1` consolidates the secure Termux agent, mobile TUI, bounded runtime, local orchestrator and optional Android LiteRT-LM broker into a release candidate.

Near-term priorities:

- complete first-user release validation;
- publish signed checksums with release artifacts;
- add real-device screenshots and accessibility review;
- broaden deterministic Android broker compatibility tests;
- improve contributor-facing examples without weakening safety controls.

Historical changes live in [`CHANGELOG.md`](CHANGELOG.md).

## Contributing and security

Contributions are welcome. Start with [`CONTRIBUTING.md`](CONTRIBUTING.md), use the issue templates, and include reproducible evidence for behavior changes.

Do not post API keys, tokens, private file paths, raw audit databases or personal storage listings in issues. Potential vulnerabilities should follow [`SECURITY.md`](SECURITY.md).

Community behavior is governed by [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Update and uninstall

```bash
bash update.sh
bash uninstall.sh
```

Uninstall preserves configuration, approvals, audit logs and trash metadata by default. Full data removal requires:

```bash
bash uninstall.sh --purge-data
```

and the exact interactive phrase `DELETE COMPTEXT DATA`.

## License

CompText Phone Agent is available under the [MIT License](LICENSE).
