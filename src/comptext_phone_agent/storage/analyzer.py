from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import time
from ..models import FileRecord, ScanResult

class StorageAnalyzer:
    def __init__(self, result: ScanResult):
        self.result = result
    def largest_files(self, limit: int = 30) -> list[FileRecord]:
        return sorted((x for x in self.result.files if not x.scan_error), key=lambda x: x.size, reverse=True)[:limit]
    def old_files(self, days: int = 365, limit: int | None = None) -> list[FileRecord]:
        cutoff = time.time() - days * 86400
        values = sorted((x for x in self.result.files if x.mtime and x.mtime < cutoff), key=lambda x: x.mtime)
        return values[:limit] if limit else values
    def recent_files(self, days: int = 30) -> list[FileRecord]:
        cutoff = time.time() - days * 86400
        return sorted((x for x in self.result.files if x.mtime >= cutoff), key=lambda x: x.mtime, reverse=True)
    def empty_files(self) -> list[FileRecord]:
        return [x for x in self.result.files if x.size == 0 and not x.scan_error]
    def by_type(self) -> dict[str, dict[str, int]]:
        groups: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "size": 0})
        for item in self.result.files:
            if not item.scan_error:
                groups[item.category]["count"] += 1
                groups[item.category]["size"] += item.size
        return dict(sorted(groups.items(), key=lambda pair: pair[1]["size"], reverse=True))
    def directory_sizes(self, limit: int = 30) -> list[tuple[str, int]]:
        sizes: dict[str, int] = defaultdict(int)
        root = Path(self.result.root)
        for item in self.result.files:
            if item.scan_error:
                continue
            path = Path(item.absolute_path)
            for parent in path.parents:
                if parent == root.parent:
                    break
                sizes[str(parent)] += item.size
                if parent == root:
                    break
        return sorted(sizes.items(), key=lambda pair: pair[1], reverse=True)[:limit]
    def recommendations(self) -> list[str]:
        recommendations = []
        archives = sum(x.size for x in self.result.files if x.category == "archive" and not x.exclusion_reason)
        apks = sum(x.size for x in self.result.files if x.category == "apk" and not x.exclusion_reason)
        if archives:
            recommendations.append(f"Review old archives; unprotected archive volume: {archives} bytes.")
        if apks:
            recommendations.append(f"Review old APK installers; unprotected APK volume: {apks} bytes.")
        if self.empty_files():
            recommendations.append(f"Review {len(self.empty_files())} empty files.")
        return recommendations or ["No obvious safe cleanup candidate was detected."]
