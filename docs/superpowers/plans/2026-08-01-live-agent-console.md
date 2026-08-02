# Live Agent Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Stabilize the mobile TUI and add live runtime-event rendering, command actions, and repeatable viewport verification.

**Architecture:** AgentRuntime emits every durable RuntimeEvent through an optional callback after persistence. PhoneAgentApp receives events through Textual's thread bridge and incrementally updates one widget per tool call. A pure diagnostic module powers `tui-doctor` without starting the UI.

**Tech Stack:** Python 3.13/3.14, Textual 1.x, Typer, SQLite, pytest.

## Global Constraints

- Preserve Termux and Python 3.14 compatibility.
- No Temporal server on Android; durable behavior remains SQLite-backed.
- Unknown event types must render safely and never execute UI-provided code.
- Existing approval and safe-mode boundaries remain unchanged.

---

### Task 1: TUI diagnostics
- [x] Add pure terminal/environment diagnostics and `tui-doctor` CLI command.
- [x] Cover compact/wide/desktop classification and JSON output.
- [x] Commit.

### Task 2: Live runtime events
- [x] Add optional event callback to AgentRuntime after durable append.
- [x] Add unit tests proving ordered callbacks and persistence-before-callback.
- [x] Commit.

### Task 3: Incremental transcript projection
- [x] Key tool cards by call ID and update existing widgets in place.
- [x] Stream model/tool/run events into the TUI while work is active.
- [x] Commit.

### Task 4: Command palette and status controls
- [x] Add a compact in-app command palette for common safe actions.
- [x] Preserve keyboard-first mobile operation and status drawer.
- [x] Commit.

### Task 5: Viewport verification and release
- [x] Test 40x20, 55x28, 72x32, 90x36, and 120x40 viewports.
- [x] Update docs/version, run fresh-install verification, package release.
- [x] Merge to main and clean temporary worktree.
