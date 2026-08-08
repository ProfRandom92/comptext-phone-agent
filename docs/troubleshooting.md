# Troubleshooting

## `~/storage/shared` is missing

Run `termux-setup-storage`, accept the Android prompt, and restart Termux. Verify with `ls ~/storage/shared`.

## `Android/data` is unreadable

This is expected on current Android releases. The agent records the scan error. It does not use root or attempt a bypass.

## Termux:API command unavailable

Install the companion app and package from compatible sources:

```bash
pkg install termux-api
comptext-phone doctor
```

Mock commands remain available with `--mock`.

## Installer reports non-Termux environment

Run `bash install-termux.sh` inside Termux. For development CI or a Linux sandbox only, use `bash install-termux.sh --sandbox`.

## Python is older than 3.12

Update Termux packages:

```bash
pkg update
pkg upgrade
pkg install python
```

## Package compilation requests Rust

Confirm the repository still pins `pydantic==1.10.25`. Remove a stale virtual environment and reinstall:

```bash
rm -rf .venv
bash install-termux.sh
```

## rclone is missing

Dry-run planning works without rclone. Actual remote execution requires:

```bash
pkg install rclone
rclone config
```

The application never runs `rclone config` automatically.

## Approval is rejected

Create a new plan. Tokens are intentionally rejected after expiry, use, plan edits, path changes, destination changes, or trash-content changes.

## Protected CompText path is blocked

This is the expected default. Natural-language instructions cannot override CompText protection. Review `config.yaml` only when a deliberate policy change is required.

## Scan is interrupted by Samsung battery optimization

Keep Termux in the foreground and exempt it from battery optimization for long scans. The project intentionally does not install a persistent background service.

## Dashboard command exits with code 5

This is intentional in 0.6.1. The legacy dashboard source is retained for migration work, but dashboard dependencies are not shipped. Use the CLI or Textual TUI until the web stack has been migrated to Pydantic 2 and a supported FastAPI release.

## Reset application code but keep data

```bash
bash uninstall.sh
bash install-termux.sh
```

Normal uninstall preserves configuration, audit database, approval history, and reports. `--purge-data` requires typing the exact destructive phrase.
