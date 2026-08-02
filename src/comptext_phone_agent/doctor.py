from __future__ import annotations
from pathlib import Path
import os, platform, shutil, sys
from typing import Any

TERMUX_COMMANDS = [
    "termux-battery-status", "termux-wifi-connectioninfo", "termux-volume",
    "termux-notification", "termux-clipboard-get", "termux-clipboard-set",
    "termux-tts-speak", "termux-vibrate",
]

def run_doctor(storage_root: Path | None = None) -> dict[str, Any]:
    home = Path.home()
    root = storage_root or home / "storage/shared"
    disk_target = root if root.exists() else home
    usage = shutil.disk_usage(disk_target)
    prefix = os.environ.get("PREFIX", "")
    checks = {
        "python": {"ok": sys.version_info >= (3, 12), "value": platform.python_version()},
        "architecture": {"ok": platform.machine().lower() in {"aarch64", "arm64", "x86_64"}, "value": platform.machine()},
        "termux_environment": {"ok": "com.termux" in prefix or bool(os.environ.get("TERMUX_VERSION")), "value": prefix or "not detected"},
        "storage_root": {"ok": root.exists(), "value": str(root)},
        "storage_writable": {"ok": root.exists() and os.access(root, os.W_OK), "value": str(root)},
        "free_bytes": {"ok": usage.free > 100 * 1024 * 1024, "value": usage.free},
        "rclone": {"ok": shutil.which("rclone") is not None, "value": shutil.which("rclone")},
        "fish": {"ok": shutil.which("fish") is not None, "value": shutil.which("fish")},
        "termux_api_package": {"ok": any(shutil.which(x) for x in TERMUX_COMMANDS), "value": {x: bool(shutil.which(x)) for x in TERMUX_COMMANDS}},
    }
    checks["overall_ok"] = all(x["ok"] for key, x in checks.items() if key in {"python", "architecture", "free_bytes"})
    return checks
