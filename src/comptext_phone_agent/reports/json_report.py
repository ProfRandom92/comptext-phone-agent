from __future__ import annotations
import json
from ..models import ScanResult
from ..storage.analyzer import StorageAnalyzer
from ..storage.duplicates import DuplicateGroup

def render_json(result: ScanResult, duplicates: list[DuplicateGroup] | None = None) -> str:
    analyzer = StorageAnalyzer(result)
    payload = result.to_dict()
    payload["summary"] = {
        "largest_files": [x.to_dict() for x in analyzer.largest_files(30)],
        "largest_directories": analyzer.directory_sizes(20),
        "file_types": analyzer.by_type(),
        "old_files": [x.to_dict() for x in analyzer.old_files(365, 30)],
        "duplicates": [x.to_dict() for x in duplicates or []],
        "recommendations": analyzer.recommendations(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
