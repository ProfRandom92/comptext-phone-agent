# Verified 0.6.1 baseline import

Date: 2026-08-02

## Import rule

The baseline was freshly extracted from the SHA-256 and CRC-verified full archive. Of its
158 normalized files, 157 were imported byte-for-byte. Every imported file was re-hashed
after copying and matched the archive inventory.

One file was excluded:

- `src/comptext_phone_agent/ollama_chat.py.before-tools`
  - Reason: accidental superseded backup, not an importable Python module or release input.
  - Backup SHA-256: `0019fa5ab7bd97794b9fe61dff4cc58b7103ccefb46a9ae414e4397f368829e5`
  - Live file SHA-256: `c7c01b94c56414257e4262201bc3d27034798cb97c5d2b91ccb53769efc5dbd5`
  - Evidence: the 6029-byte backup is an older form of the 11032-byte live module; the live
    file adds the fixed allow-listed local tool mapping and remains the shipped implementation.

No other archive member was removed or rewritten. Test-created `__pycache__`, `.pyc`, and
editable-install egg metadata existed only in disposable staging and were never copied.

## Safety scans

- ZIP traversal/absolute/drive/backslash path violations: 0
- Recognized GitHub, OpenAI, AWS, and private-key signatures: 0
- Broader high-confidence assigned-secret patterns: 0
- APK/AAB, keystore, model, database, private-key, or certificate files: 0
- Accidental backup files in the full archive: 1, excluded above

The phone-source-only `outside-secret.txt`, two `before-dashboard-fix` backups, and generated
egg metadata are not part of the authoritative full archive and were not imported.

## Baseline verification

Native Windows Python 3.12.10 with the pinned dependencies collected 118 tests but produced
four environment-specific failures: two because Windows destination syntax selected the
`rclone` path and two because fixtures assumed POSIX path separators. This run was retained
as diagnostic evidence and was not treated as the compatible baseline result.

Fresh compatible result:

- Ubuntu WSL 2
- Python 3.12.3
- pytest 9.0.3
- Pydantic 1.10.25
- `python -m compileall -q src`: exit 0
- full `python -m pytest -ra`: **117 passed, 1 skipped, 0 failed in 36.69 seconds**
- skip: optional dashboard disabled by its existing Termux Python 3.14 marker

The suite ran from the native Linux source checkout, with dependencies isolated in a
task-scoped user cache. No production source was changed to obtain the green result.

The baseline `git diff --check` excludes only
`src/comptext_phone_agent/runtime/store.py`, whose final blank line is present in the
verified archive and is deliberately retained byte-for-byte. All added evidence files
pass the whitespace check.
