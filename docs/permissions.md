# Android permissions

## Shared storage

Run once inside Termux:

```bash
termux-setup-storage
```

Approve the Android dialog. Termux then exposes convenience links under `~/storage/`, commonly including:

- `~/storage/shared`
- `~/storage/downloads`
- `~/storage/dcim`
- `~/storage/pictures`
- `~/storage/music`
- `~/storage/movies`

The agent defaults to `~/storage/shared`. Change `storage_roots` only to paths that Termux can actually read.

## Scoped Storage limits

Modern Android may deny or partially expose:

- `/Android/data`
- `/Android/obb`
- private app sandboxes
- media owned by applications that have not granted access

The scanner records failures instead of treating them as empty directories. No root workaround is attempted.

## Termux:API

Install both compatible components from the same distribution source:

1. the Termux application;
2. the Termux:API companion application;
3. the `termux-api` package inside Termux.

```bash
pkg install termux-api
comptext-phone doctor
```

Android may request notification, microphone, or other permissions depending on the command. This project does not request microphone or screen-control access.

## Samsung battery settings

For long foreground scans, exclude Termux from aggressive battery optimization when Android terminates it prematurely. The agent does not install a background service and does not use systemd.

## Sensitive content

Clipboard reads are only executed by the explicit `device clipboard-get` command. Clipboard contents are not placed in audit parameters. SSH keys, `.env` files, and key-like paths are protected from upload by default.
