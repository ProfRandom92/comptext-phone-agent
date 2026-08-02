#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

SANDBOX=0
[[ "${1:-}" == "--sandbox" ]] && SANDBOX=1
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/comptext-phone-agent"
CONFIG_FILE="$CONFIG_HOME/config.yaml"
DATA_HOME="${COMPTEXT_PHONE_HOME:-$HOME/.comptext-phone-agent}"
BIN_DIR="${COMPTEXT_PHONE_BIN_DIR:-$HOME/.local/bin}"
LOG="$DATA_HOME/install.log"

mkdir -p "$DATA_HOME" "$CONFIG_HOME"
exec > >(tee -a "$LOG") 2>&1

echo "[CompText] install started"
echo "root=$ROOT"
echo "sandbox=$SANDBOX"

if [[ "$SANDBOX" -eq 0 ]]; then
  if [[ -z "${PREFIX:-}" || "$PREFIX" != *"com.termux"* ]]; then
    echo "Error: This installer must run inside Termux, or use --sandbox." >&2
    exit 10
  fi
  case "$(uname -m)" in
    aarch64|arm64) ;;
    *) echo "Warning: designed for ARM64; detected $(uname -m)" ;;
  esac
  command -v pkg >/dev/null || { echo "Termux pkg command not found"; exit 11; }
  pkg update -y
  pkg install -y python git termux-api
else
  command -v python3 >/dev/null || { echo "python3 not found"; exit 11; }
fi

PYTHON="$(command -v python3 || command -v python)"
"$PYTHON" - <<'PY'
import sys
if sys.version_info < (3, 12):
    raise SystemExit("Python 3.12+ is required")
print("Python", sys.version.split()[0])
PY

if [[ ! -d "$VENV" ]]; then
  "$PYTHON" -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel
cd "$ROOT"
"$VENV/bin/python" -m pip install -e '.[test,tui]'

if [[ ! -f "$CONFIG_FILE" ]]; then
  cp "$ROOT/config/default.yaml" "$CONFIG_FILE"
  if [[ "$SANDBOX" -eq 1 ]]; then
    MOCK_ROOT="$ROOT/mock-phone"
    python3 - "$CONFIG_FILE" "$DATA_HOME" "$MOCK_ROOT" <<'PY'
from pathlib import Path
import sys, yaml
path=Path(sys.argv[1]); data=yaml.safe_load(path.read_text())
data["data_dir"]=sys.argv[2]
data["storage_roots"]=[sys.argv[3]]
data["trash_dir"]=str(Path(sys.argv[3]) / ".CompTextTrash")
data["termux_api"]["mock"]=True
path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
PY
  fi
else
  echo "Existing config preserved: $CONFIG_FILE"
fi

mkdir -p "$DATA_HOME/reports" "$DATA_HOME/tokens"
WRAPPER="$BIN_DIR/comptext-phone"
mkdir -p "$(dirname "$WRAPPER")"
cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
export COMPTEXT_PHONE_CONFIG="$CONFIG_FILE"
export COMPTEXT_PHONE_HOME="$DATA_HOME"
exec "$VENV/bin/comptext-phone" "\$@"
EOF
chmod +x "$WRAPPER"
CHAT_WRAPPER="$BIN_DIR/comptext-chat"
cat > "$CHAT_WRAPPER" <<EOF
#!/usr/bin/env bash
export COMPTEXT_PHONE_CONFIG="$CONFIG_FILE"
export COMPTEXT_PHONE_HOME="$DATA_HOME"
[[ -f "$CONFIG_HOME/ollama.env" ]] && source "$CONFIG_HOME/ollama.env"
exec "$VENV/bin/comptext-chat" "\$@"
EOF
chmod 700 "$CHAT_WRAPPER"

if [[ "$SANDBOX" -eq 1 ]]; then
  COMPTEXT_PHONE_CONFIG="$CONFIG_FILE" COMPTEXT_PHONE_HOME="$DATA_HOME" "$VENV/bin/python" "$ROOT/scripts/create_mock_phone.py" "$ROOT/mock-phone"
fi

echo "wrapper=$WRAPPER"
echo "config=$CONFIG_FILE"
echo "data=$DATA_HOME"
COMPTEXT_PHONE_CONFIG="$CONFIG_FILE" COMPTEXT_PHONE_HOME="$DATA_HOME" "$VENV/bin/comptext-phone" doctor --json || true
echo "[CompText] install completed"
