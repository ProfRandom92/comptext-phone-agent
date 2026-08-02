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

No cloud fallback is permitted. Broker URLs must use HTTP loopback with an explicit port,
no userinfo, path prefix, query, or fragment. `COMPTEXT_BROKER_TOKEN` is sent only to the
fixed `/v1/route` endpoint. The client never follows redirects, limits input to 16 KiB and
streamed responses to 64 KiB, requests identity encoding, rejects encoded responses, and
retains raw response bytes only up to the configured bound. Errors contain no response
bodies, tokens, or stack traces. `auto` falls back only for `network`, `timeout`, or
explicitly classified `service_unavailable` failures and marks the source as
`keyword_fallback`; authentication, authorization, redirect, malformed/schema-invalid,
rate-limit, policy, and request-size failures remain errors. A successful broker delegation
is not replaced.

JSON output may be plain, fenced, or surrounded by explanatory text, but must contain
exactly one decision object. Multiple objects, unknown fields, non-finite confidence,
non-canonical action names, Unicode confusables, and schema-invalid arguments are rejected.
The action catalog is pinned to the seven trusted actions rather than every registered tool.

Preview is default. `--execute` is required. State-changing actions require a bound,
single-use, expiring approval covering user, session, action, target, normalized arguments,
risk class, and plan hash.
