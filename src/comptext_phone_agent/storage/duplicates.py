from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from ..models import FileRecord, ScanResult
from .scanner import partial_hash, sha256_file
from .hash_cache import HashCache

@dataclass(slots=True)
class DuplicateGroup:
    kind: str
    sha256: str | None
    size: int
    files: list[str]
    protected: list[str]
    def to_dict(self) -> dict:
        return asdict(self)

class DuplicateDetector:
    def __init__(self, cache: HashCache | None = None): self.cache=cache
    def _digest(self, path: Path, kind: str) -> str:
        if self.cache:
            cached=self.cache.get(path,kind)
            if cached: return cached
        value=partial_hash(path) if kind=="partial" else sha256_file(path)
        if self.cache: self.cache.put(path,kind,value)
        return value
    def find(self, result: ScanResult, verify: bool = True) -> list[DuplicateGroup]:
        by_size: dict[int, list[FileRecord]] = defaultdict(list)
        for item in result.files:
            if not item.scan_error and not item.is_symlink:
                by_size[item.size].append(item)
        groups: list[DuplicateGroup] = []
        for size, candidates in by_size.items():
            if len(candidates) < 2:
                continue
            by_partial: dict[str, list[FileRecord]] = defaultdict(list)
            for item in candidates:
                try:
                    key = self._digest(Path(item.absolute_path), "partial")
                except OSError:
                    continue
                by_partial[key].append(item)
            for partial, possible in by_partial.items():
                if len(possible) < 2:
                    continue
                if verify:
                    by_full: dict[str, list[FileRecord]] = defaultdict(list)
                    for item in possible:
                        try:
                            digest = self._digest(Path(item.absolute_path), "sha256")
                            item.sha256 = digest
                            by_full[digest].append(item)
                        except OSError:
                            continue
                    sets = by_full.items()
                else:
                    sets = [(None, possible)]
                for digest, exact in sets:
                    if len(exact) < 2:
                        continue
                    names = {x.name for x in exact}
                    kind = "same_name_same_content" if len(names) == 1 else "same_content_different_name"
                    groups.append(DuplicateGroup(kind, digest, size, [x.absolute_path for x in exact], [x.absolute_path for x in exact if x.exclusion_reason]))
        # Same-name/different-content groups are informational.
        by_name: dict[str, list[FileRecord]] = defaultdict(list)
        for item in result.files:
            if not item.scan_error:
                by_name[item.name.lower()].append(item)
        for name, candidates in by_name.items():
            if len(candidates) < 2:
                continue
            hashes = {x.sha256 or self._digest(Path(x.absolute_path), "sha256") for x in candidates if not x.is_symlink}
            if len(hashes) > 1:
                groups.append(DuplicateGroup("same_name_different_content", None, sum(x.size for x in candidates), [x.absolute_path for x in candidates], [x.absolute_path for x in candidates if x.exclusion_reason]))
        return groups
