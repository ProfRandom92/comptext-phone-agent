#!/usr/bin/env sh
set -eu

root=$(git rev-parse --show-toplevel)
git -C "$root" config core.hooksPath .githooks
if command -v chmod >/dev/null 2>&1; then
  chmod +x "$root/.githooks/pre-commit" "$root/.githooks/pre-push"
fi
printf '%s\n' "Git hooks installed from $root/.githooks"
