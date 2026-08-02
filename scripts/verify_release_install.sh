#!/usr/bin/env bash
set -Eeuo pipefail

dist=${1:?release directory is required}
version=${2:?release version is required}
prefix="comptext-phone-agent-$version"
stage=$(mktemp -d)
case "$stage" in
  /tmp/*|/var/tmp/*) ;;
  *) echo "Refusing unsafe temporary path: $stage" >&2; exit 2 ;;
esac
cleanup() { rm -rf -- "$stage"; }
trap cleanup EXIT

install_root="$stage/install"
backup_root="$stage/rollback-copy"
config_root="$stage/config"
data_root="$stage/data"
bin_root="$stage/bin"
mkdir -p "$install_root" "$config_root" "$data_root" "$bin_root"

unzip -q "$dist/$prefix-full.zip" -d "$install_root"
install_root="$install_root/$prefix"
env \
  XDG_CONFIG_HOME="$config_root" \
  COMPTEXT_PHONE_HOME="$data_root" \
  COMPTEXT_PHONE_BIN_DIR="$bin_root" \
  bash "$install_root/install-termux.sh" --sandbox

config_file="$config_root/comptext-phone-agent/config.yaml"
test -f "$config_file"
test -x "$bin_root/comptext-phone"
env COMPTEXT_PHONE_CONFIG="$config_file" COMPTEXT_PHONE_HOME="$data_root" \
  "$bin_root/comptext-phone" config validate

python3 - "$config_file" <<'PY'
from pathlib import Path
import sys, yaml
path = Path(sys.argv[1])
data = yaml.safe_load(path.read_text(encoding="utf-8"))
data["scan"]["old_days"] = 777
path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
PY

cp -a "$install_root" "$backup_root"
upgrade_root="$stage/upgrade"
mkdir -p "$upgrade_root"
unzip -q "$dist/$prefix-upgrade.zip" -d "$upgrade_root"
cp -a "$upgrade_root/$prefix/." "$install_root/"
env XDG_CONFIG_HOME="$config_root" COMPTEXT_PHONE_HOME="$data_root" COMPTEXT_PHONE_BIN_DIR="$bin_root" \
  bash "$install_root/update.sh"

python3 - "$config_file" <<'PY'
from pathlib import Path
import sys, yaml
value = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))["scan"]["old_days"]
if value != 777:
    raise SystemExit("upgrade overwrote the existing configuration")
PY

mv "$install_root" "$stage/upgraded-copy"
mv "$backup_root" "$install_root"
env XDG_CONFIG_HOME="$config_root" COMPTEXT_PHONE_HOME="$data_root" COMPTEXT_PHONE_BIN_DIR="$bin_root" \
  bash "$install_root/update.sh"
env COMPTEXT_PHONE_CONFIG="$config_file" COMPTEXT_PHONE_HOME="$data_root" \
  "$bin_root/comptext-phone" config validate

printf '%s\n' "clean install, overlay upgrade, configuration preservation, and rollback passed"
