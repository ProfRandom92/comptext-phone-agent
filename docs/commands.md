# Command reference

## System and configuration

```bash
comptext-phone doctor [--path PATH] [--json]
comptext-phone status [--json]
comptext-phone config show [--json]
comptext-phone config validate
```

## Storage analysis

```bash
comptext-phone scan [--path PATH] [--top 30] [--hash] [--json]
comptext-phone analyze large [--path PATH] [--top 30] [--json]
comptext-phone analyze old [--path PATH] [--top 30] [--json]
comptext-phone analyze types [--path PATH] [--json]
comptext-phone duplicates [--path PATH] [--verify] [--json]
```

`--verify` completes the duplicate pipeline with full SHA-256. No duplicate command modifies files.

## Cleanup and approvals

```bash
comptext-phone cleanup plan --path PATH --old-days 365 --json
comptext-phone cleanup approve PLAN_ID --phrase APPROVE --json
comptext-phone cleanup apply PLAN_ID [--token TOKEN] [--dry-run] [--json]
```

Plans select only unprotected old APK, archive, temporary, or cache candidates. Apply moves them to the internal trash; it does not permanently delete them.

## Trash

```bash
comptext-phone trash list [--json]
comptext-phone trash restore ITEM_ID --phrase APPROVE [--json]
comptext-phone trash purge [--plan-id PLAN_ID] [--token TOKEN] [--phrase "DELETE PERMANENTLY"] [--json]
```

Restore is class 1. Purge is class 3 and is bound to the exact active trash contents in the stored plan.

## Backup

```bash
comptext-phone backup plan --path FILE --destination TARGET --json
comptext-phone backup approve PLAN_ID --phrase APPROVE --json
comptext-phone backup apply PLAN_ID --dry-run --json
comptext-phone backup apply PLAN_ID --execute [--token TOKEN] --json
```

A target containing `:` is treated as rclone, for example `gdrive:Phone` or `nextcloud:Phone`. A normal filesystem path is a local target. Local copies are atomic and hash-verified. Source files are never removed after backup.

## Device

```bash
comptext-phone device battery [--mock] [--json]
comptext-phone device wifi [--mock] [--json]
comptext-phone device volume [--mock] [--json]
comptext-phone device notify --title TITLE --content TEXT [--mock]
comptext-phone device clipboard-get [--mock] [--json]
comptext-phone device clipboard-set TEXT [--mock]
comptext-phone device tts TEXT [--mock]
comptext-phone device vibrate --duration-ms 250 [--mock]
```

All commands have timeouts. Clipboard reads happen only after the explicit command.

## Reports, audit, agent, and dashboard

```bash
comptext-phone report --path PATH --format markdown|json|html [--output FILE]
comptext-phone audit [--limit 100] [--json]
comptext-phone audit show ID [--json]
comptext-phone chat --provider mock|openai|openrouter|gemini|nvidia-nim|local
comptext-phone serve
comptext-phone demo [--path ./mock-phone]
```

The default agent provider is mock/deterministic and requires no key. Optional provider output is constrained to typed, non-executing intents.

## Exit codes

- `0`: success
- `1`: missing audit item or generic command failure
- `2`: doctor found a blocking local prerequisite
- `3`: approval or safety policy blocked the request
- `4`: Termux:API failure
- `5`: dashboard dependency failure
- `6`: provider configuration or response failure
