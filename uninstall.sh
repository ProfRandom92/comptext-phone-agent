#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FULL=0
[[ "${1:-}" == "--purge-data" ]] && FULL=1
rm -f "$HOME/.local/bin/comptext-phone" "$HOME/.local/bin/comptext-chat"
rm -rf "$ROOT/.venv"
if [[ "$FULL" -eq 1 ]]; then
  read -r -p "Type DELETE COMPTEXT DATA to remove configuration, audit logs and tokens: " answer
  [[ "$answer" == "DELETE COMPTEXT DATA" ]] || { echo "Data purge cancelled."; exit 3; }
  rm -rf "${XDG_CONFIG_HOME:-$HOME/.config}/comptext-phone-agent" "${COMPTEXT_PHONE_HOME:-$HOME/.comptext-phone-agent}"
else
  echo "Configuration and data preserved."
fi
echo "Uninstall complete."
