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

## Optional local dashboard

The dashboard is deliberately optional so the default Termux installation keeps a smaller dependency and attack surface.

From the repository directory:

```bash
./.venv/bin/python -m pip install -e '.[dashboard]'
comptext-phone serve
```

`serve` prints a loopback URL and a generated session token to the local terminal, then starts Starlette through Uvicorn. Valid dashboard hosts are restricted by configuration to `127.0.0.1`, `localhost`, or `::1`; externally reachable bind addresses are rejected.

The dashboard requires the session token for protected reads, additionally requires CSRF for POST scan requests, constrains requested paths to configured storage roots, uses no external CDN, and exposes no unrestricted cleanup/delete/upload/shell endpoint.

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

The core pins `pydantic==1.10.25` intentionally. Pydantic 2 requires the Rust-based `pydantic-core` runtime, while native Termux is not the same binary-wheel target as conventional manylinux ARM64. Keeping the core on the pure-Python Pydantic 1 line avoids introducing a Rust/native-wheel requirement into the primary Android installation path.

The optional web layer uses `starlette==1.5.0` and `uvicorn==0.51.0` directly. This restores the dashboard on a supported, audited stack without requiring FastAPI or Pydantic 2 in Termux.
