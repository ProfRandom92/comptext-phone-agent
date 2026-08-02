# CompText Phone Agent 0.6.1 verification

Source: user-exported phone installation archive, SHA-256
`7b61e8cd42c8fd8d8406b9543d37621bee85e3321b6e522cc9bf5513411dbec6`.

## Applied maintenance fixes

- Unified `pyproject.toml`, package runtime and CLI status version at `0.6.1`.
- Fresh Termux installs and updates now install `.[test,tui]`.
- Made the optional TUI package lazy-loadable so core CLI commands still import without Textual.
- Added Pydantic v1/v2 compatibility for configuration validation.
- Removed stale egg-info, dashboard-fix backups and `outside-secret.txt` test artifact.

## Executed checks

- `112 passed, 7 warnings in 2.40s` for core, CLI, storage, approval, audit,
  orchestrator and runtime tests available without the optional Textual package.
- `python -m compileall -q src tests` completed successfully.
- `bash -n` completed successfully for installer, updater, uninstaller and start script.
- Both release ZIP archives passed `unzip -t`.

## Environment limitation

The build container did not have the optional Textual dependency and had no outbound
package index access. Textual-specific interaction tests were therefore not rerun in
this container. Their source and the previously phone-tested TUI are included unchanged,
while the TUI install path itself is corrected in this release.
