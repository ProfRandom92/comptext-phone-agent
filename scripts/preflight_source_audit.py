from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

FORBIDDEN_SUFFIXES = {
    ".apk", ".aab", ".jks", ".keystore", ".litertlm", ".tflite",
    ".gguf", ".safetensors", ".db", ".sqlite", ".sqlite3",
}
SECRET_PATTERNS = {
    "github_token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    "openai_key": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "aws_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(rb"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not re.match(r"^[A-Za-z]:", name)
        and "\\" not in name
    )


def normalized_member_names(infos: list[zipfile.ZipInfo]) -> dict[str, str]:
    files = [i.filename.rstrip("/") for i in infos if not i.is_dir()]
    first_parts = {PurePosixPath(name).parts[0] for name in files if PurePosixPath(name).parts}
    strip_root = len(first_parts) == 1 and all(len(PurePosixPath(name).parts) > 1 for name in files)

    result: dict[str, str] = {}
    for original in files:
        parts = PurePosixPath(original).parts
        normalized = PurePosixPath(*parts[1:]).as_posix() if strip_root else PurePosixPath(*parts).as_posix()
        result[original] = normalized
    return result


def inspect_archive(path: Path) -> dict:
    raw = path.read_bytes()
    result = {
        "file": path.name,
        "sha256": sha256_bytes(raw),
        "size_bytes": len(raw),
        "zip_integrity": "ok",
        "entries": {},
        "unsafe_paths": [],
        "forbidden_files": [],
        "secret_matches": [],
    }
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            result["zip_integrity"] = f"failed:{bad}"

        name_map = normalized_member_names(archive.infolist())
        for info in archive.infolist():
            if info.is_dir():
                continue
            original = info.filename
            if not safe_name(original):
                result["unsafe_paths"].append(original)
                continue
            normalized = name_map[original]
            data = archive.read(info)
            result["entries"][normalized] = {
                "source_member": original,
                "sha256": sha256_bytes(data),
                "size_bytes": len(data),
            }
            if Path(normalized).suffix.lower() in FORBIDDEN_SUFFIXES:
                result["forbidden_files"].append(normalized)
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(data):
                    result["secret_matches"].append({"path": normalized, "pattern": label})
    return result


def compare(left: dict, right: dict) -> dict:
    left_entries = left["entries"]
    right_entries = right["entries"]
    left_paths = set(left_entries)
    right_paths = set(right_entries)
    common = left_paths & right_paths
    changed = sorted(
        path for path in common
        if left_entries[path]["sha256"] != right_entries[path]["sha256"]
    )
    identical = sorted(common - set(changed))
    return {
        "only_left": sorted(left_paths - right_paths),
        "only_right": sorted(right_paths - left_paths),
        "changed": changed,
        "identical_count": len(identical),
        "common_count": len(common),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("archive-audit.json"))
    args = parser.parse_args()

    reports = [inspect_archive(path) for path in args.archives]
    comparisons = {}
    for index, left in enumerate(reports):
        for right in reports[index + 1:]:
            comparisons[f'{left["file"]}::{right["file"]}'] = compare(left, right)

    payload = {"archives": reports, "comparisons": comparisons}
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(args.output)
    return 1 if any(
        r["zip_integrity"] != "ok"
        or r["unsafe_paths"]
        or r["secret_matches"]
        for r in reports
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
