# Secure Ollama tool chat

The chat sends natural-language messages and JSON tool schemas to Ollama Cloud. Tool
calls are accepted only when the name exists in the local `ToolRegistry`. Arguments are
validated by the registry and paths are fixed to the configured storage root.

Read-only tools include storage scan, duplicate detection, largest/old files, battery
and Wi-Fi. The only modifying-adjacent tool is `cleanup_plan`; it persists a plan but
sets `changed=false` and still requires the normal local approval workflow.

Chat sessions and messages are stored in the existing SQLite state database. Secrets
are not stored in chat rows. The latest provider/model session is resumed by default.

## Provider configuration and diagnostics

Provider settings have one precedence order: command-line options, YAML configuration,
environment variables, then documented defaults. The chat and TUI accept `--provider`,
`--model`, and `--base-url`. The corresponding environment variables are
`COMPTEXT_AGENT_PROVIDER`, `COMPTEXT_AGENT_MODEL`, and `COMPTEXT_AGENT_BASE_URL`.
The timeout can be set with `COMPTEXT_AGENT_TIMEOUT_SECONDS` when the YAML timeout is
left at its default.
Legacy `OLLAMA_MODEL` and `OLLAMA_HOST` remain supported for Ollama Cloud.

The default is `ollama-cloud` with `gpt-oss:20b`; it does not select a Pro-only Qwen
model. Run `comptext-phone provider-doctor --json` to see the effective non-secret
settings and whether a credential is configured. Credentials are never printed.
There is no silent cloud fallback: an explicitly selected unsupported chat provider is
reported as a configuration error. The credential-free keyword orchestrator remains
available independently through `comptext-phone orchestrator route`.

## Runtime and TUI

Use `comptext-phone tui` for the mobile-first Textual interface. Use `comptext-phone chat --simple` as the lightweight fallback. Add `--safe-mode` to disable all planning or mutation-capable tools.
