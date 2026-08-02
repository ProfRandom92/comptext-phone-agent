# Plugins, Skills, and Hooks

## Plugins and phase

- Superpowers: design, plan, worktree, TDD, debugging, execution, review, verification
- CodeRabbit: review coherent diffs and fix-review cycles
- Codex Security: threat model, repository scan, diff scan, validation, attack paths, fixes
- GitHub: private repository import, commits, workflow and artifact inspection
- Test Android Apps: ADB/emulator QA after APK build
- Build Android Apps: emulator browser and interactive UI inspection after APK build
- Compoosioo: external app discovery and GitHub fallback operations

Record whether each requested skill was discovered, read, invoked, or manually replaced.

## Hooks

Version:

```text
.githooks/pre-commit
.githooks/pre-push
scripts/install-git-hooks.sh
```

Pre-commit stays fast:

- `git diff --check`
- changed-file formatting/lint
- secret scan
- model/keystore/database/large-binary rejection

Pre-push runs moderate checks:

- compileall
- focused or full Python tests
- lint/type checks
- Android unit tests when Android paths changed
- forbidden-file scan

CI is authoritative. Hooks may be bypassed with standard `--no-verify`, but CI must still
reject the violation.
