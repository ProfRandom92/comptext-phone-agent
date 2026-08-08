# Termux setup

## Supported installation source

Use a current Termux build and a matching Termux:API companion from F-Droid or the official GitHub release channel. Do not mix signing sources because Android will reject incompatible companion applications.

## Storage permission

```bash
termux-setup-storage
```

Approve the Android permission prompt, then verify:

```bash
ls -la ~/storage/shared
```

## Installation

From the repository directory:

```bash
bash install-termux.sh
```

The installer verifies Termux, checks architecture and Python, installs required Termux packages, creates `.venv`, installs the local project, preserves an existing config, creates runtime directories, installs `~/.local/bin/comptext-phone`, and runs the doctor.

It does not execute remote `curl | bash` installers.

## Shell startup

Bash or Zsh:

```bash
./start.sh doctor
```

Fish:

```fish
./start.fish doctor
```

Ensure `~/.local/bin` is in `PATH` for direct use:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## First checks

```bash
comptext-phone doctor
comptext-phone config validate
comptext-phone scan --path ~/storage/shared --top 30
comptext-phone duplicates --path ~/storage/shared --verify
```

## Termux:API

```bash
pkg install termux-api
comptext-phone device battery
comptext-phone device wifi
comptext-phone device volume
```

The application remains usable if Termux:API is absent; only device commands fail with a clear exit code.

## rclone

```bash
pkg install rclone
rclone config
```

Configure rclone interactively. The agent never prints the config file or secrets. Always create and inspect a backup plan before approval.

## Dependency portability

Pydantic 1.10.25 is pinned because it has a universal pure-Python distribution, adds minimal Python 3.14 support, and does not require `pydantic-core`. The 0.6.1 release does not ship dashboard dependencies; `comptext-phone serve` fails closed until the web stack is migrated to Pydantic 2 and a supported FastAPI release.
