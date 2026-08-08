# Portable Dashboard Migration Design

## Goal

Re-enable the local CompText Phone Agent dashboard on a supported 2026 web stack without weakening its local-only, token, CSRF, path-boundary, approval, redaction, audit, or Termux-portability guarantees.

## Starting state

The verified 0.6.1 release candidate intentionally disables `comptext-phone serve` because the legacy FastAPI/Starlette line was not acceptable after dependency audit. The repository retains the dashboard source and security integration tests, but the `dashboard` extra is empty in that release candidate.

## Investigation and architecture pivot

The first migration attempt moved the entire core to Pydantic 2 and used current FastAPI + Uvicorn. Linux CI proved that stack functionally sound and the dependency audit was clean.

That approach was rejected before completion because CompText Phone Agent's primary deployment target is native Termux on Android. Pydantic 2 requires the Rust-backed `pydantic-core` package, while Termux is not a conventional manylinux ARM64 target and native Python extensions may require platform-specific packaging or compilation work. Making the core depend on Pydantic 2 would therefore trade a working pure-Python Termux path for a less predictable native build path.

The selected architecture keeps the Termux core on `pydantic==1.10.25` and migrates the dashboard directly to Starlette.

Exact dashboard dependency targets:

- `starlette==1.5.0`
- `uvicorn==0.51.0`

Test-only HTTP client support:

- `httpx2==2.7.0`

The existing runtime `httpx==0.28.1` dependency is left unchanged in this PR so provider/broker networking is not mixed into the dashboard migration.

## Why Starlette directly

Starlette provides the routing, request, response, application, and TestClient primitives this small loopback dashboard needs. The dashboard does not use FastAPI dependency injection, automatic OpenAPI generation, or Pydantic request models deeply enough to justify forcing FastAPI's Pydantic 2 dependency line into the Android runtime.

This approach:

- restores a maintained web interface;
- avoids mandatory `pydantic-core` on Termux;
- keeps web dependencies optional;
- preserves the smaller default CLI/TUI runtime surface;
- keeps the security model explicit and testable.

## Core model contract

The existing `CompatModel` remains on Pydantic 1.10.25 with `extra = "forbid"` and compatibility helpers for `model_validate()` / `model_dump()` call sites. Existing validation semantics must remain unchanged:

- dashboard host restricted to `127.0.0.1`, `localhost`, or `::1`;
- orchestrator router URL restricted to strict loopback HTTP;
- environment-variable naming constrained;
- minimum confidence in `[0.0, 1.0]`;
- unknown configuration keys forbidden.

## Dashboard runtime

`comptext-phone serve` imports Uvicorn and `create_app` lazily so base installations do not import optional web dependencies.

The command must:

- use the validated dashboard host and port;
- print only the loopback URL and generated local session token to stderr;
- start Uvicorn with `reload=False` and `access_log=False`;
- never bind to an externally reachable address;
- never persist dashboard credentials;
- fail with a clear install instruction when the dashboard extra is absent.

## API security invariants

The Starlette dashboard remains intentionally narrow:

- protected GET views require `X-CompText-Token`;
- POST scan additionally requires `X-CompText-CSRF`;
- token comparisons use `secrets.compare_digest`;
- storage paths are constrained to configured storage roots;
- `/api/scan` is POST-only and GET returns 405;
- no cleanup/apply/delete/upload/shell execution endpoint is exposed;
- the HTML is self-contained and uses no external CDN.

## CI and audit contract

Python CI installs `.[test,tui,dashboard]` so dashboard tests execute instead of skipping.

Security CI installs `.[test,dashboard]`, then runs `pip check`, `pip-audit`, repository guards, and Bandit. This ensures Starlette, Uvicorn, and their transitive dependencies are included in the audited environment.

## TDD evidence strategy

Regression coverage must prove:

1. the optional dashboard dependency set is exact and excludes FastAPI / `pydantic-core`;
2. invalid non-loopback dashboard hosts remain rejected;
3. the five dashboard security integration tests execute;
4. `serve` invokes Uvicorn with the configured loopback host/port, `reload=False`, and `access_log=False`;
5. the generated session token is non-empty and printed only as local startup output;
6. active docs no longer claim the dashboard is intentionally disabled;
7. full Python and security CI remain green.

## Release interaction

This work is stacked on `docs/community-release-0.6.1` but must not be merged into that release branch or `main` automatically. It is a post-0.6.1 feature line; versioning can be decided when the verified 0.6.1 community-release PR has landed.
