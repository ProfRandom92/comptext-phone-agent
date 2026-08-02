# Secure Ollama tool chat

The chat sends natural-language messages and JSON tool schemas to Ollama Cloud. Tool
calls are accepted only when the name exists in the local `ToolRegistry`. Arguments are
validated by the registry and paths are fixed to the configured storage root.

Read-only tools include storage scan, duplicate detection, largest/old files, battery
and Wi-Fi. The only modifying-adjacent tool is `cleanup_plan`; it persists a plan but
sets `changed=false` and still requires the normal local approval workflow.

Chat sessions and messages are stored in the existing SQLite state database. Secrets
are not stored in chat rows. The latest provider/model session is resumed by default.

## Runtime 0.3 and TUI

Use `comptext-phone tui` for the mobile-first Textual interface. Use `comptext-phone chat --simple` as the lightweight fallback. Add `--safe-mode` to disable all planning or mutation-capable tools.
