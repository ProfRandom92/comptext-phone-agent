# CompText Phone Agent Runtime 0.3

The 0.3 runtime adds a bounded multi-step agent loop, versioned hash-chained events, durable runs, local artifacts, safe mode, context compaction, and a Textual TUI.

## Commands

```bash
comptext-phone tui
comptext-phone tui --safe-mode
comptext-phone chat --simple
comptext-phone chat --safe-mode
```

Safe mode exposes only built-in read-only tools. Unknown tools, paths outside configured storage roots, model-generated shell commands, and mutation tools are rejected before execution.

## Loop limits

- 6 model turns
- 8 tool calls
- 2 identical calls
- 300 seconds

Runs stop with an auditable reason when a limit is reached. Approval requests persist as `waiting_approval`; the runtime never keeps a blocking approval thread alive.

## Persistence

Existing 0.2 SQLite databases migrate automatically. Added tables store runs, events, and artifacts. Chat summaries are added to existing session rows without deleting messages.

## Event integrity

Every runtime event stores its parent hash and its own SHA-256 hash. `runtime_event_to_air()` projects runtime events into an explicit CompText AIR evidence shape without storing hidden reasoning.


## 0.4 responsive TUI

The TUI uses an event reducer and trusted card factory. Widths below 60 columns use compact mode; 60-89 use wide mode; 90 and above display the desktop sidebar. Local durable signals (`cancel`, `approve`, `reject`, `resume`) and deterministic tool idempotency keys are stored in SQLite. No Temporal cluster is required on the phone.


### Live event delivery

`AgentRuntime.run(..., event_callback=...)` persists each event before invoking the callback. The Textual client bridges callbacks to the UI thread and updates existing tool widgets by durable call ID. SQLite remains the source of truth for replay and resume.


## Local Orchestrator 0.6

The orchestrator separates planning from action routing. `Gemma-4-E2B-it` is the intended planner role and `MobileActions-270M` is the intended action-router role. The current Termux package includes the trusted catalog, parser, policy service, keyword fallback, diagnostics, and a loopback-only broker client. Google AI Edge Gallery models remain isolated inside the Gallery app unless a separate local broker exposes them.

Only these first-party actions are published initially: storage scan, duplicate scan, largest files, old files, battery, Wi-Fi, and cleanup-plan creation. No mutation action is exposed by the router catalog.
