# Orchestrator Contract

Pipeline:

```text
User input
→ deterministic keyword router or authenticated local broker
→ typed RouteDecision
→ static ActionCatalog
→ strict argument validation
→ RuntimePolicy
→ preview / approval / execution / planner delegation
→ audit
```

Trusted actions:

- `scan_storage`
- `find_duplicates`
- `largest_files`
- `old_files`
- `device_battery`
- `device_wifi`
- `cleanup_plan`

Route kinds: `direct_action`, `delegate`, `clarify`, `reject`.

The decision contains canonical fields `kind`, `action`, `arguments`, `confidence`,
`reason`, and `source`. Confidence must be finite and within 0..1. A direct action requires
a known catalog action. Malformed or ambiguous model output never executes.

Router modes:

- `keyword`: deterministic and credential-free
- `broker`: authenticated loopback OpenAI-compatible endpoint
- `auto`: broker first, deterministic keyword only as fallback

No cloud fallback is permitted. Broker URLs must use HTTP loopback, no userinfo, no token
query parameter, bounded timeout/response size, and no external redirect.

Preview is default. `--execute` is required. State-changing actions require a bound,
single-use, expiring approval covering user, session, action, target, normalized arguments,
risk class, and plan hash.
