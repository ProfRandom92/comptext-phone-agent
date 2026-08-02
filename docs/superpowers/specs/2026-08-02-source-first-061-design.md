# CompText Phone Agent 0.6.1 Source-first Hardening Design

## Decision

The full 0.6.1 archive is the authoritative baseline. The empty private GitHub repository
receives an immutable baseline import before any optimization. The phone-source and
upgrade archives are comparison evidence, not replacement sources.

## Architecture

The monorepo has two products:

1. Python/Termux agent: storage and device tools, approvals, audit, runtime, TUI, chat
   providers, and deterministic/local broker orchestration.
2. Android broker: a separately buildable native application providing authenticated
   loopback LiteRT-LM inference.

They communicate through a narrow OpenAI-compatible loopback protocol. Policy and action
execution remain in the Termux agent.

## Work streams

### A. Baseline preservation

Verify archives, compare trees and hashes, exclude only generated or unsafe files, run the
existing suite, and create the first `main` commit.

### B. Provider and version cleanup

Remove stale hard-coded application versions and duplicated Ollama model defaults.
Centralize effective provider/model resolution:

CLI option → application config → environment → documented non-Pro fallback.

Never silently change model after an access error. Surface 401, 403, 404, 429, timeout,
and network failures distinctly. Keep local orchestration available without cloud access.

### C. Orchestrator hardening

Preserve the seven trusted actions. Strengthen typed route validation, JSON extraction,
Unicode/whitespace normalization, response limits, loopback-only URLs, redirect handling,
confidence bounds, policy integration, approvals, audit, and redaction.

### D. Android broker

Implement the smallest secure broker that can import, load, unload, and invoke verified
`.litertlm` models. It exposes health, model status, route, and chat endpoints and never
executes device actions.

### E. Engineering harness

Add concise AGENTS files, current official references, fast local hooks, full CI, security
scans, deterministic packaging, checksums, and evidence reports.

## Error handling

All external/provider and broker failures use typed categories and stable machine-readable
JSON. Client-visible errors contain no stack traces or secrets. Model unavailability must
not trigger hidden cloud or model substitution.

## Testing

Preserve every existing test. Add contract, provider-precedence, security, broker, Android,
upgrade, and release tests. Test counts must never shrink without a documented deletion
review.

## Success criteria

- Full baseline imported unchanged except recorded exclusions.
- Existing full suite passes.
- Version and provider display are accurate.
- Qwen Pro-only defaults are removed.
- Local keyword orchestration remains credential-free.
- Android project builds and passes unit/lint checks.
- Security review has no unresolved validated high/critical finding.
- CI and release artifacts are reproducible.
