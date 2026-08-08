# Pydantic 2 Dashboard Migration Design

## Goal

Re-enable the local CompText Phone Agent dashboard on a supported 2026 web stack without weakening its local-only, token, CSRF, path-boundary, approval, redaction, or audit guarantees.

## Current state

The 0.6.1 release candidate intentionally disables `comptext-phone serve` because the legacy FastAPI/Starlette dependency line was not acceptable after security audit. The repository still contains the dashboard application and integration tests, but `dashboard = []` means those tests are skipped unless FastAPI is installed separately.

The core configuration layer also carries a Pydantic v1/v2 compatibility shim and v1-style `@validator` calls, while `ProviderBackedPlanner` still uses `parse_obj`.

## Chosen approach

Perform a native Pydantic 2 migration and restore the dashboard as an explicit optional extra.

Exact dependency targets for this migration:

- `pydantic==2.13.4`
- `fastapi==0.139.2`
- `uvicorn==0.51.0`

FastAPI remains optional through the `dashboard` extra; normal CLI/TUI installs do not acquire a web server unless the user explicitly installs `.[dashboard]`.

## Alternatives rejected

1. **Keep internal models on `pydantic.v1` while adding modern FastAPI.** This would preserve a compatibility layer indefinitely and create two model semantics inside one process. It also increases future migration cost.
2. **Run the dashboard in a separate virtual environment/process.** This isolates dependencies but adds packaging, lifecycle, authentication, update, and support complexity disproportionate to a loopback-only local dashboard.

## Model migration

`CompatModel` becomes a direct Pydantic 2 base model using `ConfigDict(extra="forbid")`. Its custom `model_validate()` and `model_dump()` compatibility methods are removed.

All v1 `@validator` decorators become `@field_validator`. `ProviderBackedPlanner` uses `Intent.model_validate(...)` rather than `parse_obj(...)`.

No validation semantics may change:

- dashboard host remains loopback-only;
- orchestrator router URL remains strict loopback HTTP;
- environment-variable naming remains constrained;
- minimum confidence remains within `[0.0, 1.0]`;
- unknown configuration keys remain forbidden.

## Dashboard runtime

`comptext-phone serve` imports `uvicorn` and `create_app` lazily so non-dashboard installations do not import optional web dependencies.

The command must:

- use the configured dashboard host and port;
- rely on configuration validation to restrict the host to `127.0.0.1`, `localhost`, or `::1`;
- create the existing app with the normal application context;
- print the generated local session token to stderr before startup;
- start Uvicorn without auto-reload;
- never bind to an externally reachable address;
- never add a mutation endpoint that bypasses the existing CSRF/token controls.

## API security invariants

The existing dashboard API remains intentionally narrow:

- GET views require `X-CompText-Token`;
- POST scan additionally requires `X-CompText-CSRF`;
- storage paths are constrained to configured storage roots;
- there is no dangerous GET scan endpoint;
- the dashboard does not add cleanup/apply/delete/upload execution endpoints.

## Test strategy

TDD regression coverage must prove:

1. dashboard dependencies are explicitly declared;
2. Pydantic 2 model validation preserves all existing config constraints;
3. the dashboard integration suite executes rather than skips when the extra is installed;
4. `serve` invokes Uvicorn with the configured loopback host/port and no reload;
5. `serve` exposes the session token only through local stderr startup output;
6. existing Python tests, installation verification, dependency audit, and security checks stay green.

## Release interaction

This work is intentionally stacked on top of `docs/community-release-0.6.1` but must not be merged into that release branch automatically. It is the next-feature line after the verified 0.6.1 candidate, so PR review can decide whether it becomes 0.6.2 or 0.7.0 after the community-release PR lands.
