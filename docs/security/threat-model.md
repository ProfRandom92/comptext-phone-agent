# Defensive Threat Model

Updated: 2026-08-02

## Assets and trust boundaries

- User files and CompText action approvals remain owned by the Python/Termux application.
- Broker bearer tokens, imported model records, and model binaries are app-private Android
  data and are excluded from backup and device transfer.
- Model output, imported documents, HTTP request bodies, and all caller-provided JSON are
  untrusted.
- The Android broker is an inference boundary, not an action-execution boundary. It has no
  shell, Android-intent, contacts, calendar, or arbitrary file-operation endpoint.

## Threats and controls

| Threat | Defensive control | Verification |
|---|---|---|
| Remote/LAN access | Ktor connector host is the fixed literal `127.0.0.1`; no remote host setting or cloud fallback exists. | Source review and strict host test; runtime bind remains unverified because no emulator reached ADB. |
| Credential theft or replay | 256-bit random bearer token; AES-GCM wrapping key held by Android Keystore; token hidden by default; explicit regeneration invalidates the prior token; no token logging. | Source/static review; Keystore runtime remains emulator-unverified. |
| Oversized/chunked request exhaustion | Content-Length precheck and incremental channel reads retain no more than 256 KiB. Encoded request bodies are rejected. | Bounded accumulator regression test and source review. |
| Schema confusion or model-output injection | Duplicate keys, trailing JSON, unknown fields, invalid roles, non-finite confidence, and noncanonical actions are rejected. Broker output never authorizes execution. | Protocol regression tests; Python catalog/policy/approval suite. |
| Inference denial of service | Fixed rate window, one active inference, one queued request, bounded prompt/output configuration, and timeout. | Rate-limit and coordinator regression tests. |
| Unsafe model import/path traversal | Visible SAF selection only; normalized `.litertlm` filename; plausible size; streaming SHA-256; fsync; required atomic rename; partial cleanup; app-private directory. HTTP import returns `interactive_required`. | Atomic import and model-policy regression tests. |
| Engine lifecycle leaks or replacement races | One lifecycle mutex; old engine closed before replacement; conversations and engine explicitly closed; service unloads on destruction. | Source review and successful compile against inspected LiteRT-LM 0.15.0 signatures; real model load remains unverified. |
| Background persistence or hidden service | Explicit activity/notification action only; non-sticky service; no boot receiver; persistent stoppable notification; `specialUse` declaration and permission. | Manifest/lint review; runtime notification remains unverified. |
| Exported component/PendingIntent abuse | Only launcher activity is exported; service is not exported; PendingIntents are explicit and immutable. | Manifest/static review and lint. |
| Dependency/artifact substitution | Concrete dependency pins, Gradle lock state, SHA-256 dependency verification metadata, ignored build/model/key outputs, v2 APK signature verification. | Fresh Gradle gates, metadata generation, secret-pattern review, and `apksigner`. |

## Residual and unavailable evidence

- The platform cybersecurity safety gate blocked the requested Codex Security plugin scan;
  it was not retried and no completed plugin scan is claimed.
- CodeRabbit could not execute on this Windows/WSL host. Ordinary full-file review, tests,
  lint, dependency locking/checksums, and secret-pattern checks were used instead.
- Emulator installation, UI frames, loopback calls, notification behavior, Keystore use,
  real `.litertlm` import/load/inference, and logcat review are unverified because available
  disk space was below the emulator's minimum userdata requirement.
