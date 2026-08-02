from __future__ import annotations
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
import hashlib, mimetypes, os
from ..models import FileRecord, ScanResult
from .exclusions import ExclusionEngine
from .hash_cache import HashCache

CATEGORY_MAP = {
    ".jpg":"image",".jpeg":"image",".png":"image",".gif":"image",".webp":"image",".heic":"image",
    ".mp4":"video",".mkv":"video",".avi":"video",".mov":"video",".webm":"video",
    ".mp3":"audio",".wav":"audio",".flac":"audio",".m4a":"audio",".ogg":"audio",
    ".pdf":"document",".doc":"document",".docx":"document",".xls":"document",".xlsx":"document",
    ".ppt":"document",".pptx":"document",".txt":"document",".md":"document",
    ".zip":"archive",".tar":"archive",".gz":"archive",".7z":"archive",".rar":"archive",
    ".apk":"apk",".tmp":"temporary",".temp":"temporary",".cache":"cache",
}

def classify(path: Path) -> str:
    return CATEGORY_MAP.get(path.suffix.lower(), (mimetypes.guess_type(path.name)[0] or "other").split("/")[0])

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()

def partial_hash(path: Path, bytes_to_read: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    size = path.stat().st_size
    with path.open("rb") as handle:
        digest.update(handle.read(bytes_to_read))
        if size > bytes_to_read:
            handle.seek(max(0, size - bytes_to_read))
            digest.update(handle.read(bytes_to_read))
    return digest.hexdigest()

class StorageScanner:
    def __init__(self, exclusions: ExclusionEngine, follow_symlinks: bool = False, hash_cache: HashCache | None = None):
        self.exclusions = exclusions
        self.follow_symlinks = follow_symlinks
        self.hash_cache = hash_cache
    def _sha256(self, path: Path) -> str:
        if self.hash_cache:
            value=self.hash_cache.get(path,"sha256")
            if value: return value
        value=sha256_file(path)
        if self.hash_cache: self.hash_cache.put(path,"sha256",value)
        return value
    def iter_files(self, root: Path, with_hash: bool = False) -> Iterator[FileRecord]:
        root = root.resolve()
        def onerror(error: OSError) -> None:
            self._walk_errors.append({"path": getattr(error, "filename", str(root)), "error": str(error)})
        self._walk_errors: list[dict[str, str]] = []
        for current, directories, filenames in os.walk(root, followlinks=self.follow_symlinks, onerror=onerror):
            current_path = Path(current)
            if not self.follow_symlinks:
                directories[:] = [d for d in directories if not (current_path / d).is_symlink()]
            for name in filenames:
                path = current_path / name
                try:
                    is_link = path.is_symlink()
                    if is_link and not self.follow_symlinks:
                        stat = path.lstat()
                        yield FileRecord(str(path.absolute()), str(path.relative_to(root)), name, path.suffix.lower(), classify(path), stat.st_size, stat.st_mtime, stat.st_atime, root.name, exclusion_reason="symlink not followed", is_symlink=True)
                        continue
                    stat = path.stat()
                    decision = self.exclusions.evaluate(path, root)
                    yield FileRecord(
                        str(path.resolve()), str(path.relative_to(root)), name, path.suffix.lower(),
                        classify(path), stat.st_size, stat.st_mtime, stat.st_atime, root.name,
                        sha256=self._sha256(path) if with_hash else None,
                        exclusion_reason=decision.reason, is_symlink=is_link,
                    )
                except (OSError, ValueError) as error:
                    yield FileRecord(str(path.absolute()), str(path), name, path.suffix.lower(), classify(path), 0, 0, None, root.name, scan_error=str(error), is_symlink=path.is_symlink())
    def scan(self, root: Path, with_hash: bool = False) -> ScanResult:
        started = datetime.now(timezone.utc).isoformat()
        files = list(self.iter_files(root, with_hash=with_hash))
        return ScanResult(str(root.resolve()), started, datetime.now(timezone.utc).isoformat(), files, list(self._walk_errors))
