# CompText Phone Agent 0.6.1

Maintenance release rebuilt from the verified phone source archive.

## Fixes

- Aligns package, runtime, and CLI version metadata at `0.6.1`.
- Installs the Textual TUI in fresh Termux installs and updates.
- Keeps the core CLI importable when the optional TUI dependency is absent.
- Removes stale build metadata, backup manifests, and local test artifacts from release archives.
- Preserves user configuration, state, audit data, chat history, and API-key files during upgrades.

## Integrity

Release archives are generated deterministically from the cleaned source tree and accompanied by SHA-256 checksums.
