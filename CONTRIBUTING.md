# Contributing to CompText Phone Agent

Thank you for helping improve CompText Phone Agent. The project prioritizes safety, reproducibility and Android/Termux portability over convenience shortcuts.

## Before you start

- Search existing issues and pull requests.
- Keep changes focused and avoid unrelated refactors.
- Never weaken approval, path-protection, redaction or audit behavior to simplify a feature.
- Do not include API keys, tokens, private paths, personal file listings, audit databases or device identifiers in issues, commits or test fixtures.

## Development setup

```bash
git clone https://github.com/ProfRandom92/comptext-phone-agent.git
cd comptext-phone-agent
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test,tui]'
pytest
```

For the Android broker, use its checked-in Gradle wrapper from `android-broker/`.

## Change requirements

A pull request should include:

1. a clear problem statement;
2. a narrowly scoped implementation;
3. tests for new behavior or regression coverage;
4. documentation updates where commands or safety boundaries change;
5. evidence that relevant tests passed;
6. an explicit statement about security and data-mutation impact.

Runtime changes must preserve these invariants:

- read-only analysis remains the default;
- mutating actions are represented as typed plans;
- approvals remain expiring, single-use and plan-bound;
- protected paths are checked before execution;
- model output cannot become unrestricted shell execution;
- secrets and sensitive values are redacted from logs and reports.

## Test commands

```bash
pytest
python scripts/preflight_source_audit.py
```

Run Android checks from the broker directory when applicable:

```bash
cd android-broker
./gradlew test lint assembleDebug
```

## Commit and pull-request style

Use concise imperative commit messages, for example:

```text
feat: add deterministic storage fixture
test: cover expired approval token
docs: clarify scoped storage limitation
```

Complete the pull-request template. Screenshots and logs must be sanitized before upload.

## Reporting security problems

Do not open a public issue for a suspected vulnerability. Follow [SECURITY.md](SECURITY.md).
