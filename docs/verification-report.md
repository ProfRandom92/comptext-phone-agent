# Verified sandbox report — CompText Phone Agent 0.1.0

Verification date: 2026-08-01

## Environment

- Composio isolated Linux sandbox
- Python 3.13.13
- Architecture: x86_64
- Project target: Termux ARM64 on Android, primarily Samsung Galaxy A33
- Physical Android device available during verification: no

The sandbox verifies application logic, installation behavior, CLI, mock device integration, reports, security policy, approvals, backup wrappers, and dashboard behavior. Android Scoped Storage and real Termux:API behavior still require an on-device acceptance test.

## Dependency portability

The clean installer resolved the pinned direct dependencies, including Pydantic 1.10.24 and FastAPI 0.125.0. `pydantic_core` was explicitly checked and was absent, so the project does not require a Rust toolchain for Pydantic configuration validation.

## Commands executed

```bash
bash install-termux.sh --sandbox
comptext-phone --help
comptext-phone doctor
comptext-phone demo
comptext-phone scan --path ./mock-phone --top 30 --json
comptext-phone analyze large --path ./mock-phone --json
comptext-phone duplicates --path ./mock-phone --verify --json
comptext-phone cleanup plan --path ./mock-phone --json
comptext-phone report --format markdown
comptext-phone report --format json
comptext-phone report --format html
comptext-phone device battery --mock --json
comptext-phone device wifi --mock --json
comptext-phone chat --provider mock --message "Analysiere meinen Speicher und ändere nichts."
pytest -o addopts='' -ra
python scripts/verify_install.py
```

## Installer and CLI

- Fresh sandbox installer: passed.
- Repeated installer on an existing mock phone: passed after restoring write permission on the deliberately unreadable fixture.
- Existing configuration preservation: verified.
- CLI help: passed and exposed all top-level command groups.
- `scripts/verify_install.py`: `installation verification passed`.
- Update without configured Git upstream: passed and updated only the local editable installation.
- Normal uninstall: removed venv and wrapper while preserving config and runtime data.

The doctor correctly reported that the verification host was not Termux and did not have real Termux:API, rclone, or Fish. These optional device checks did not invalidate sandbox operation.

## Mock storage results

- Files scanned: 17
- Logical byte total: 8,663,126
- Duplicate groups: 2
- Cleanup candidates: 4
- Estimated cleanup bytes: 81,941
- CompText paths detected as protected: yes
- Symlink outside scan root followed: no
- Reports generated:
  - Markdown: 3,575 bytes
  - JSON: 26,789 bytes
  - HTML: 3,121 bytes
- HTML external network references: none

The duplicate report identified an exact same-content video pair with the DCIM original marked protected, plus equal filenames with different content.

## Approval and action results

1. Cleanup apply without approval returned exit code 3 and changed nothing.
2. Class-1 approval with `APPROVE` moved all four planned files to the internal trash.
3. Restore without a confirmation phrase returned exit code 3.
4. Restore with `APPROVE` succeeded.
5. A direct attempt to modify `CompText/critical-project.zip` was blocked with `protected CompText path`.
6. A plan changed after approval was rejected.
7. An expired approval was rejected.
8. A consumed approval token was rejected on reuse.
9. The protected CompText file remained present.
10. Class-3 purge without the destructive phrase returned exit code 3.
11. Purge using the exact stored plan and `DELETE PERMANENTLY` removed three remaining trash items.

## Backup results

- Nextcloud-style rclone target dry-run: passed, no remote or local change.
- Local target plan: approved and executed.
- Local copy: atomic `.part` workflow used.
- SHA-256 comparison: matched.
- Source file retained after backup: yes.
- Existing local destination default strategy: skip.
- Missing rclone, timeout, failure, dry-run, no-source-deletion, and protected-upload behavior: covered by tests.

## Dashboard results

- Bind configuration restricted to loopback.
- Unauthenticated status request: HTTP 403.
- Authenticated status request: HTTP 200.
- GET on scan action: HTTP 405.
- POST scan without CSRF: HTTP 403.
- POST scan with session and CSRF headers: HTTP 200.
- `/etc` outside configured storage root: HTTP 403.
- Status, storage, duplicates, plans, approvals, trash, backups, audit, and reports views: HTTP 200.
- External CDN dependency: none.

## Audit and redaction

Audit events were written to SQLite with WAL enabled. A test event containing an API key, password, and bearer value was stored with recursive redaction. The original secret strings were absent from queried audit data.

## Test result

```text
collected 74 items
74 passed in 1.33s
```

Coverage groups included configuration, scanner/analyzer, duplicates, paths/exclusions, approval expiry/mutation/replay, trash/restore, backup/local hashing, Termux:API, provider adapters, CLI smoke tests, executor integration, and dashboard session/CSRF/root constraints.

## Known limitations

- No physical Samsung Galaxy A33 or Android ARM64 device was available in the sandbox.
- Real Termux:API companion compatibility and Android permission prompts were not executable here.
- `/Android/data` accessibility varies by Android release and user-granted storage access.
- Long scan resume checkpoints are not implemented in version 0.1.0; scans are restartable but begin again.
- Remote rclone execution was not performed because it would require an external configured account; dry-run, command construction, retries, timeout, and error paths were verified.
- The local dashboard is operational and mobile responsive but intentionally minimal rather than a full SPA.


## Git history

The verified repository was committed as a sequence of focused changes:

- `chore: initialize termux phone agent`
- `feat: add storage scanner and reports`
- `feat: add duplicate detection and cleanup planning`
- `feat: add approval engine and safe trash`
- `feat: add termux api backup agent and dashboard`
- `test: add security and integration coverage`
- `docs: complete termux installation and verification guides`
- `chore: finalize package metadata`
