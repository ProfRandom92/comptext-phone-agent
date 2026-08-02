# Release Contract

Repository remains private.

Required workflows:

- Python CI for Python 3.12 and 3.13
- Android CI with JDK 21, unit tests, lint, and debug APK
- Security CI with dependency, secret, and static checks
- Manual release workflow

Use least-privilege `GITHUB_TOKEN` permissions and pin third-party actions to complete
commit SHAs.

Required artifacts:

- `comptext-phone-agent-0.6.1-full.zip`
- `comptext-phone-agent-0.6.1-upgrade.zip`
- `comptext-phone-agent-0.6.1-source.zip`
- Android debug APK
- checksums
- JSON manifest

Exclude model binaries, secrets, databases, audit data, keystores, SDK paths, virtual
environments, worktrees, caches, and build directories. Verify ZIP CRC, SHA-256, clean
installation, upgrade, APK signature, and archive contents.
