from __future__ import annotations
from typing import Any
import re

SENSITIVE = re.compile(r"(api[_-]?key|token|secret|password|passwd|authorization|cookie|rclone_config|clipboard)", re.I)
BEARER = re.compile(r"(?i)bearer\s+[a-z0-9._~+/-]+=*")
KEYLIKE = re.compile(r"(?i)(sk-[a-z0-9_-]{8,}|AIza[a-z0-9_-]{10,})")

def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("<redacted>" if SENSITIVE.search(str(key)) else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, str):
        return KEYLIKE.sub("<redacted>", BEARER.sub("Bearer <redacted>", value))
    return value
