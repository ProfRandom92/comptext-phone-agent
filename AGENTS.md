# CompText Phone Agent — Repository Agent Instructions

## Mission

Maintain the complete CompText Phone Agent as a secure, local-first Android and Termux
assistant with durable runtime state, approvals, audit logging, storage analysis,
responsive TUI, explicit cloud-provider configuration, local routing, and native
LiteRT-LM inference.

## Source-of-truth map

- Design: `docs/superpowers/specs/2026-08-02-source-first-061-design.md`
- Plan: `docs/superpowers/plans/2026-08-02-source-first-061-plan.md`
- Orchestrator: `docs/architecture/orchestrator-contract.md`
- Android broker: `docs/architecture/android-broker-contract.md`
- Security: `docs/security/security-contract.md`
- Testing: `docs/testing/test-matrix.md`
- Release: `docs/release/release-contract.md`
- Official references: `docs/OFFICIAL_SOURCES.md`
- Plugin/skill/hook usage: `docs/execution/plugins-skills-hooks.md`
- Android subtree: `android-broker/AGENTS.md`

## Non-negotiable rules

- Preserve existing 0.6.1 behavior unless a test and documented decision justify change.
- Read-only and preview are defaults.
- No file deletion or movement without explicit, bound approval.
- Model output is untrusted data, never executable code.
- No arbitrary shell commands, Python imports, Android intents, or model-defined tools.
- No implicit cloud access and no silent provider/model fallback.
- The local keyword router must function without cloud credentials.
- Every action comes from a static catalog and strict schema.
- No access outside configured storage roots.
- Never log API keys, bearer tokens, approval secrets, raw clipboard content, or private
  file content.
- The Android broker performs inference only and executes no CompText actions.
- Never commit secrets, model files, keystores, databases, user reports, SDK paths,
  virtual environments, caches, or build outputs.

## Engineering workflow

For every non-trivial change:

1. inspect current implementation and relevant tests
2. update or confirm the written contract
3. write a failing test
4. run it and record the expected failure
5. implement the smallest correct change
6. run focused tests
7. run the full relevant suite
8. review the diff
9. run security checks
10. update documentation
11. commit coherently
12. verify before integration

Use systematic debugging before changing code after any unexpected failure.

## Git

- Canonical repository: `ProfRandom92/comptext-phone-agent`
- Visibility: public
- Baseline import: `main`
- Development branches: use task-specific branches from the current target branch; do not reuse completed feature branches
- Worktrees: use an isolated task-specific worktree; do not reuse completed feature worktrees
- No force-push
- Final `git status --short` must be empty

## Definition of done

Done requires full existing-suite compatibility, new focused tests, compile/lint/type
checks, security review, Android build evidence where applicable, installation and
upgrade verification, reproducible release artifacts, GitHub push, CI inspection,
and an explicit list of remaining hardware-only checks.
