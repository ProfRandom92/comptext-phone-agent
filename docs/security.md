# Security model

## Default posture

The default operating mode is `analysis`. It permits recursive reads, metadata inspection, hashing, duplicate detection, reports, and read-only device checks. It rejects file modifications, uploads, overwrites, and deletion.

## Risk classes

| Class | Meaning | Requirement |
|---:|---|---|
| 0 | Read-only | No approval |
| 1 | Reversible local change | Exact plan plus `APPROVE` |
| 2 | External upload or larger batch | Explicit plan review plus `APPROVE` |
| 3 | Permanent deletion or overwrite | Controlled mode plus `DELETE PERMANENTLY` |

`--yes` is intentionally not used to bypass class 3.

## Approval binding

Each approval contains installation ID, user ID, session ID, action types, source paths, destination paths, file count, total size, plan hash, issue/expiry times, risk class, and nonce. Tokens use HMAC-SHA256 with a locally generated `0600` key.

Verification rejects:

- token signature changes;
- another installation, user, or session;
- plan edits after approval;
- changed paths, targets, counts, sizes, or risk;
- expired tokens;
- replay of an already consumed token;
- revoked or unknown approvals.

## Protected paths

CompText path protection is a hard policy default. A path component containing `comptext` is read-only relative to the configured scan root. Normal agent requests cannot disable this. Other defaults protect DCIM, Pictures, WhatsApp, Android, Samsung, SSH material, `.env`, Git repositories, virtual environments, and project dependency trees.

Rules support exact paths, globs, optional regular expressions, extensions, analyze-only categories, never-delete, and never-upload. User overrides are configuration changes, not natural-language instructions.

## Filesystem defenses

- All paths are expanded and resolved before use.
- Allowed-root containment is checked.
- NUL bytes and traversal outside configured roots are rejected.
- Symlink escape is rejected before a modifying action.
- Symlinks are not followed during normal scans.
- Trash destinations use UUIDs and timestamps to avoid collisions.
- Local backup writes to `.part`, verifies SHA-256, then atomically replaces the destination.

## Process defenses

Termux:API and rclone use argument arrays with `shell=False`, explicit timeouts, captured output, and bounded error handling. There is no general shell tool, `eval`, or arbitrary command execution exposed to the language model.

## Provider defenses

Optional providers may only return one of three validated intents: `scan`, `duplicates`, or `cleanup_plan`. Provider output is parsed as JSON into Pydantic models, normalized to the configured root, and cannot directly invoke an executor.

## Audit redaction

The logger recursively redacts key names or values associated with API keys, passwords, bearer tokens, cookies, authorization headers, clipboard content, and rclone secrets. Raw `.env` contents and rclone configuration are never logged.

## Dashboard request protection

The dashboard binds to `127.0.0.1` by default. Every API request requires the in-memory `X-CompText-Token`. POST requests additionally require `X-CompText-CSRF`. Dangerous actions are not implemented as GET requests, storage paths remain inside configured roots, and no secrets are embedded in the HTML page.

## Remaining trust boundary

Python and Termux run with the Android permissions granted to Termux. The agent cannot protect data from another process with the same Linux UID or from a compromised device. Physical-device validation remains necessary before relying on the project for important data.
