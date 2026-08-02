from __future__ import annotations
from pathlib import Path
import os

class PathSecurityError(ValueError):
    pass

def normalize_path(value: str | Path, allowed_roots: list[str | Path] | None = None, must_exist: bool = False) -> Path:
    raw = Path(os.path.expandvars(os.path.expanduser(str(value))))
    if "\x00" in str(raw):
        raise PathSecurityError("NUL byte in path")
    resolved = raw.resolve(strict=must_exist)
    if allowed_roots:
        roots = [Path(os.path.expandvars(os.path.expanduser(str(r)))).resolve() for r in allowed_roots]
        if not any(resolved == root or root in resolved.parents for root in roots):
            raise PathSecurityError(f"path outside allowed roots: {resolved}")
    return resolved

def ensure_no_symlink_escape(path: Path, allowed_root: Path) -> Path:
    root = allowed_root.resolve()
    candidate = path.resolve(strict=False)
    if not (candidate == root or root in candidate.parents):
        raise PathSecurityError("path escapes allowed root")
    cursor = path
    while cursor != root and cursor != cursor.parent:
        if cursor.exists() and cursor.is_symlink():
            target = cursor.resolve()
            if not (target == root or root in target.parents):
                raise PathSecurityError("symlink escapes allowed root")
        cursor = cursor.parent
    return candidate

def atomic_write(path: Path, data: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(data, encoding="utf-8") if isinstance(data, str) else temp.write_bytes(data)
    os.replace(temp, path)
