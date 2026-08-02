# Source archive comparison

Date: 2026-08-02

The authoritative baseline is `comptext-phone-agent-0.6.1-full.zip`. Paths below are
normalized by removing a single common ZIP root directory when present.

## Archive verification

| Archive | SHA-256 | Bytes | Files | ZIP CRC | Unsafe paths | Secret signatures | Forbidden binaries |
|---|---|---:|---:|---|---:|---:|---:|
| `comptext-phone-agent-0.6.1-full.zip` | `813efe1ff5eab69eee9859b42291fc27bc6dbc3f6660fc7137158fdf55c58fa4` | 149033 | 158 | ok | 0 | 0 | 0 |
| `comptext-phone-agent-phone-source.zip` | `7b61e8cd42c8fd8d8406b9543d37621bee85e3321b6e522cc9bf5513411dbec6` | 153042 | 163 | ok | 0 | 0 | 0 |
| `comptext-phone-agent-0.6.1-upgrade.zip` | `3995aa6170df59fc821a1c49b0754a68b35ea13832122a1773586426e3b623d0` | 140501 | 158 | ok | 0 | 0 | 0 |

The hashes match `reference/SHA256SUMS.txt`. ZIP CRC was verified by reading and testing
every member. The structured per-file inventory is in `archive-inventory.json`.

## Full versus upgrade

All 158 normalized files are byte-identical. Neither archive contains a path absent from
the other. The upgrade archive is therefore packaging evidence, not a different source
baseline.

## Full versus phone-source

There are 154 common paths: 147 byte-identical and 7 changed.

Changed paths:

- `install-termux.sh`
- `pyproject.toml`
- `src/comptext_phone_agent/__init__.py`
- `src/comptext_phone_agent/cli.py`
- `src/comptext_phone_agent/config.py`
- `src/comptext_phone_agent/tui/__init__.py`
- `update.sh`

The phone-source copy reports stale versions (`0.6.0` in `pyproject.toml` and `0.1.0` in
`__init__.py`); the full archive reports `0.6.1` in both. The full archive is used without
backporting phone-source differences.

Only in the full archive:

- `RELEASE_COMMIT.txt`
- `docs/RELEASE_0.6.1.md`
- `docs/verification-0.6.1.md`
- `tests/unit/test_release_metadata.py`

Only in phone-source:

- `outside-secret.txt`
- `pyproject.toml.before-dashboard-fix`
- `requirements-termux.txt.before-dashboard-fix`
- `src/comptext_phone_agent.egg-info/PKG-INFO`
- `src/comptext_phone_agent.egg-info/SOURCES.txt`
- `src/comptext_phone_agent.egg-info/dependency_links.txt`
- `src/comptext_phone_agent.egg-info/entry_points.txt`
- `src/comptext_phone_agent.egg-info/requires.txt`
- `src/comptext_phone_agent.egg-info/top_level.txt`

These phone-source-only files are not imported. In particular, the backup files and
generated egg metadata are comparison evidence, not authoritative source.
