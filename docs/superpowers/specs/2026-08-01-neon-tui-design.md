# CompText Phone Agent 0.4 Neon TUI Design

## Goal

Transform the functional 0.3 Textual interface into a polished responsive CompText Neon terminal UI for Android Termux, tablets, and desktop terminals without weakening the existing runtime policy, approval, privacy, or replay guarantees.

## Constraints

- Python 3.12+ and Termux Python 3.14 remain supported.
- Textual remains optional under the `tui` extra.
- The simple prompt-toolkit chat remains available.
- The model cannot create widgets, styles, commands, or arbitrary markup.
- Runtime events are projected through a fixed trusted component catalog.
- Read-only tools may run automatically; changing actions still require existing approval mechanisms.
- No Temporal server or worker runs on the phone.
- Temporal concepts are implemented locally through durable event history, deterministic state transitions, signals, idempotency keys, and resumable runs.

## Architecture

```text
RuntimeStore / RuntimeEvent
          |
          v
     EventReducer
          |
          v
       ViewState
          |
          v
      CardFactory
          |
          v
 Trusted Textual widgets
```

The TUI never calls storage or device tools directly. It submits user goals to the existing `AgentRuntime` and renders only persisted/runtime events.

## Responsive layouts

### Compact mobile: width below 60 columns

- Two-row header with logo glyph, title, time, and compact badges.
- Single transcript column.
- No persistent sidebar.
- Status drawer opened through `Ctrl+P` or command palette.
- Tool cards use compact summaries.
- Composer and footer remain visible.

### Wide mobile/tablet: width 60-89 columns

- Single transcript column with wider tool cards.
- Compact system strip beneath header.
- Status drawer remains optional.

### Desktop: width 90 columns or more

- Transcript on the left.
- Persistent status sidebar on the right.
- Full storage, model, battery, protection, and session details.

## Visual language

- OLED black and deep violet surfaces.
- Cyan for analysis and active input.
- Purple for agent identity and navigation.
- Green for completed safe states.
- Amber for approvals and warnings.
- Red only for failures or irreversible risk.
- Borders remain subtle; only the focused composer and active tool card receive stronger glow.
- Logo uses a reliable Unicode infinity fallback. Optional Chafa integration is display-only and never required.

## Trusted component catalog

- `WelcomePanel`
- `UserMessage`
- `AgentMessage`
- `GenericToolCard`
- `StorageScanCard`
- `DuplicateScanCard`
- `ApprovalCard`
- `ErrorCard`
- `StatusSidebar`
- `StatusDrawer`
- `Composer`

Unknown events render as a safe generic metadata row. Unknown tool types render as `GenericToolCard`, never executable UI.

## Temporal-style local durability

The phone keeps SQLite as the source of truth. Add:

- deterministic `RunSignal` values: cancel, approve, reject, resume;
- an idempotency key for each prepared tool call;
- durable signal records;
- resume eligibility derived from run state and last event;
- projection replay from sequence number zero;
- no network service dependency.

## Error handling

- Model/network errors render as recoverable error cards.
- Cancellation produces a durable cancellation event.
- Resize never interrupts a run.
- TUI restart rebuilds the screen from stored events.
- Missing Termux APIs produce a clear unavailable state, not a crash.
- Missing Textual continues to produce the existing install guidance.

## Testing

- Unit tests for breakpoints, reducers, card models, status projections, and signals.
- Textual pilot tests for compact and desktop dimensions.
- Tests for empty, streaming, completed tool, approval, error, and resumed states.
- Full existing regression suite.
- Fresh editable install with `[test,tui]`.
