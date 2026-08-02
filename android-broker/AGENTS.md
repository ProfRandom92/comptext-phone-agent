# Android LiteRT-LM Broker — Scoped Instructions

Applies to every file under `android-broker/`.

## Boundary

The broker is an authenticated loopback inference service. It does not execute agent
actions, shell commands, Android intents, file operations, contacts, or calendar changes.

## Network

- Bind explicitly to `127.0.0.1`.
- Never bind to `0.0.0.0`, LAN addresses, or wildcard IPv6.
- No cloud fallback or remote-server setting.
- Reject external redirects.
- Restrict cleartext networking to localhost only.

## Service lifecycle

- Start only from visible, explicit user interaction.
- Use a declared foreground-service type that current Android guidance supports for this
  special-purpose user-visible broker.
- Do not auto-start at boot.
- Prevent duplicate server instances.
- Provide a persistent, stoppable notification.
- Restore a safe state after process recreation.

## Authentication and limits

- Cryptographically random bearer token.
- Keystore-backed protection at rest.
- Token hidden by default and never logged.
- Regeneration invalidates the prior token.
- Maximum body size 256 KiB.
- Strict content type and JSON schema.
- Bounded prompt, output tokens, timeout, rate, and queue.
- One active inference.

## Models

- Router: MobileActions-270M compatible `.litertlm` artifact.
- Planner/chat: supported Gemma E2B-class `.litertlm` artifact selected from verified
  official compatibility information.
- Use the current official LiteRT-LM Kotlin API; do not guess signatures.
- Pin a concrete Maven version after resolving current metadata.
- Import via Storage Access Framework.
- Copy atomically to app-owned storage.
- Validate format and plausible size and calculate SHA-256.
- Remove partial imports.
- Close old engines before replacement.
- Model binaries never enter Git or CI artifacts.

## Required verification

- `./gradlew testDebugUnitTest`
- `./gradlew lintDebug`
- `./gradlew assembleDebug`
- APK signature verification
- emulator QA and logcat review when an emulator/device is available
