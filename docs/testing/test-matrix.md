# Test Matrix

Preserve every existing test from the full archive.

Add coverage for:

- package-version banners
- provider/model precedence
- no Pro-only Qwen fallback
- explicit provider/model diagnostics
- 401, 403, 404, 429, timeout, and network failures
- local keyword orchestration without cloud credentials
- route JSON extraction and hostile edge cases
- Unicode and whitespace action confusion
- loopback URL and redirect enforcement
- response-size limits
- approval replay/mutation
- audit redaction
- source archive comparison and forbidden files
- Android authentication, request limits, model import, model lifecycle, serialized
  inference, foreground-service lifecycle, and process recreation
- Termux install, 0.6.1 upgrade, rollback, and release archive verification

Final Python verification includes compileall, full pytest, CLI doctors, TUI doctor,
orchestrator doctor, route preview, and mock execution.

Final Android verification includes unit tests, lint, assembleDebug, APK verification, and
emulator QA where available.
