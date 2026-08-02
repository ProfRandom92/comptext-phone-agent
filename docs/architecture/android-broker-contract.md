# Android Broker Contract

The Android application provides local LiteRT-LM inference to Termux through an
authenticated loopback HTTP service.

Required endpoints:

- `GET /health`
- `GET /v1/models`
- `GET /v1/status`
- `POST /v1/route`
- `POST /v1/chat/completions`
- `POST /v1/models/import`
- `POST /v1/models/load`
- `POST /v1/models/unload`

Use current official LiteRT-LM Kotlin APIs and a pinned concrete Maven version. Compatible
models use `.litertlm`. The engine is initialized off the UI thread and closed explicitly.

The server binds only to `127.0.0.1`, requires a bearer token protected at rest through
Android Keystore, limits request size to 256 KiB, validates content type and schemas,
allows one active inference, and returns stable JSON errors without stack traces.

Model import uses Storage Access Framework and app-owned storage with temporary copy,
SHA-256 calculation, fsync/atomic rename, and partial-file cleanup.

The user explicitly starts/stops a visible foreground service. The service is not started
from the background or at boot. The manifest uses the current valid foreground-service
type and permissions for the special-purpose local inference broker.
