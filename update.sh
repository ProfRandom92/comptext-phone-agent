#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "$ROOT/.git" ]] && command -v git >/dev/null; then
  if git -C "$ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
    git -C "$ROOT" pull --ff-only
  else
    echo "No Git upstream configured; updating the local installation only."
  fi
fi
[[ -x "$ROOT/.venv/bin/python" ]] || { echo "Virtual environment missing; run install-termux.sh first." >&2; exit 12; }
cd "$ROOT"
"$ROOT/.venv/bin/python" -m pip install -e '.[test,tui]'
"$ROOT/.venv/bin/comptext-phone" config validate
echo "Update complete."
