# Changelog

All notable changes to CompText Phone Agent are documented here.

The format is based on Keep a Changelog, and the project uses semantic versioning.

## [Unreleased]

### Documentation

- Community-facing README redesign.
- Contribution, security and conduct policies.
- Structured issue and pull-request templates.
- Release evidence, checklist and first-user smoke test.

## [0.6.1] - 2026-08-02

### Fixed

- Hardened packaged rollback verification.
- Made CLI option assertions independent of terminal formatting and Click option-name variants.

### Security

- Preserved plan-bound approval, protected-path and data-preservation guarantees in packaged release verification.

## [0.6.0] - 2026-08-02

### Added

- Local two-model orchestration for Android.
- Deterministic local keyword router.
- Optional authenticated loopback Android LiteRT-LM broker.
- Fixed trusted action catalog with runtime policy checks.
- Broker routing and health diagnostics.

### Security

- Rejected remote broker hosts, raw Android intents and arbitrary shell commands.
- Restricted broker communication to fixed loopback endpoints.

## [0.5.0]

### Added

- Live Agent Console with durable runtime event rendering.
- In-place tool cards and mobile command palette.
- TUI readiness diagnostics.

## [0.4.0]

### Added

- Responsive neon mobile TUI.
- Compact, wide-mobile and desktop layouts.
- Trusted component catalog and durable local signals.

## [0.3.0]

### Added

- Bounded multi-step agent runtime.
- Hash-chained runtime events, context compaction and local artifacts.
- Textual interface and safe mode.

## [0.2.0]

### Added

- Native Ollama tool-call chat adapter.
- Prompt history, completion, slash commands and SQLite sessions.
- Partial and SHA-256 cache with invalidation.

## [0.1.0]

### Added

- Secure local-first Android storage analysis.
- Conservative duplicate detection and reporting.
- Typed cleanup plans, approvals, reversible trash and audit logging.
- Termux:API mocks, rclone backup planning and local dashboard.