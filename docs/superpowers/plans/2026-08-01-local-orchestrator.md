# Local Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe local two-model orchestrator with a fixed action catalog, FunctionGemma-compatible router parsing, loopback broker support, CLI diagnostics, and existing CompText policy enforcement.

**Architecture:** Router output is treated as untrusted typed input. `OrchestratorService` validates action identity, arguments, confidence, and policy before previewing or executing through `ToolRegistry`; complex requests remain with the planner runtime.

**Tech Stack:** Python 3.13+, Pydantic v1 compatibility layer, httpx, Typer, pytest, SQLite audit/runtime.

## Global Constraints

- No free-form shell or Android intents.
- No implicit cloud fallback.
- Broker endpoints must be loopback-only.
- Default CLI behavior is preview-only.
- All production behavior is introduced through failing tests first.

---

### Task 1: Typed Models and Parser
- [ ] Add failing tests for JSON and `call:name{...}` parser formats.
- [ ] Implement immutable route/action models and strict parser.
- [ ] Verify parser tests and commit.

### Task 2: Trusted Catalog and Router
- [ ] Add failing tests for catalog projection and German keyword routing.
- [ ] Implement catalog, keyword fallback, and loopback HTTP router.
- [ ] Verify router tests and commit.

### Task 3: Orchestrator Service and Policy
- [ ] Add failing tests for direct read-only execution, preview, planner delegation, approval plan, malformed args, and forbidden actions.
- [ ] Implement service using existing `RuntimePolicy` and `ToolRegistry`.
- [ ] Verify service tests and commit.

### Task 4: Configuration, CLI, and Diagnostics
- [ ] Add failing tests for configuration validation and CLI route preview.
- [ ] Add orchestrator config, doctor checks, and Typer subcommands.
- [ ] Verify CLI tests and commit.

### Task 5: Release and Integration
- [ ] Update docs/version to 0.6.0.
- [ ] Run complete tests, compile checks, and fresh installation.
- [ ] Build full and upgrade archives with SHA-256 checksums.
- [ ] Fast-forward merge to main, rerun full tests, clean worktree, and upload artifacts.
