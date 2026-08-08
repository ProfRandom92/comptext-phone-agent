## Summary

Describe the problem and the smallest change that solves it.

## Validation

- [ ] Relevant Python tests passed
- [ ] Android tests/lint/build passed when applicable
- [ ] Documentation was updated
- [ ] Logs, screenshots and fixtures are sanitized

Commands and results:

```text
Paste concise, sanitized evidence here.
```

## Safety impact

- [ ] Read-only behavior remains the default
- [ ] No approval, protected-path, redaction or audit boundary is weakened
- [ ] No arbitrary shell or raw Android intent execution is introduced
- [ ] Data preservation and rollback behavior are unchanged or documented

Explain any mutation, permission, secret-handling or network impact:

## Checklist

- [ ] The change is focused and contains no unrelated refactor
- [ ] New behavior has regression coverage
- [ ] No API key, token, private path, personal file listing or audit database is included
- [ ] I reviewed the diff from a first-time user's perspective