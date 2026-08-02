# CompText Local Orchestrator Design

## Goal

Build a safe two-model orchestration layer for Android: a capable planner model handles conversation and complex reasoning, while a small FunctionGemma-style router maps simple German commands to a fixed action catalog. All execution remains under CompText policy, approvals, audit logging, and idempotency controls.

## Architecture

The orchestrator receives one user request and obtains a typed `RouteDecision`. The router can return `direct_action`, `planner`, `clarify`, or `reject`. A direct action is accepted only when its name exists in the trusted catalog, arguments validate against the catalog schema, confidence meets the configured threshold, and the action's policy allows the next step. Unknown actions, malformed arguments, network hosts outside loopback, and free-form shell or Android intents are rejected.

The local Android model integration is represented by a loopback-only HTTP broker contract. This allows a future LiteRT-LM Android service to host Gemma 4 and MobileActions-270M without coupling the Termux application to Google AI Edge Gallery internals. A deterministic keyword router remains available for tests and offline fallback.

## Components

- `orchestrator/models.py`: route and action data models.
- `orchestrator/catalog.py`: trusted action catalog projected from the existing `ToolRegistry`.
- `orchestrator/parser.py`: strict FunctionGemma/JSON output parser.
- `orchestrator/router.py`: keyword router and loopback HTTP router.
- `orchestrator/service.py`: decision validation and planner/direct-action dispatch.
- `orchestrator/doctor.py`: diagnostics for router and planner endpoints.
- CLI subcommands under `comptext-phone orchestrator` for route previews and diagnostics.

## Initial Action Catalog

The first release exposes only existing safe CompText tools:

- `scan_storage`
- `find_duplicates`
- `largest_files`
- `old_files`
- `device_battery`
- `device_wifi`
- `cleanup_plan`

No arbitrary shell command, raw Android intent, package installation, file deletion, contact write, calendar write, flashlight change, clipboard write, or network mutation is exposed.

## Routing Rules

- High-confidence read-only action: execute through existing RuntimePolicy and ToolRegistry.
- Plan-only action such as `cleanup_plan`: return a plan and approval requirement; never apply changes.
- Complex or ambiguous request: route to the planner model.
- Unknown or forbidden action: reject safely and record a reason.
- Router unavailable: use deterministic fallback or planner, depending on configuration.

## Security

- Broker URLs must resolve to `127.0.0.1`, `localhost`, or `::1`.
- Router output is untrusted input and must pass parsing, catalog lookup, JSON-schema validation, and RuntimePolicy authorization.
- No implicit cloud fallback.
- Every route decision is auditable and contains no private chain-of-thought.
- Tool execution remains idempotent through the existing runtime store.

## Success Criteria

- German storage, duplicate, battery, Wi-Fi, and cleanup-plan commands route correctly.
- Ambiguous requests are delegated to the planner.
- Unknown actions and malformed arguments never reach a handler.
- Loopback broker configuration is enforced.
- CLI route preview works without executing actions by default.
- Full test suite passes on a fresh editable installation.
