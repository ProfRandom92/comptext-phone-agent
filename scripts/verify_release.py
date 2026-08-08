#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from package_release import ReleaseError, sha256_path, verify_zip


def verify_release(directory: Path, version: str) -> dict[str, object]:
    prefix = f"comptext-phone-agent-{version}"
    required = {
        f"{prefix}-full.zip",
        f"{prefix}-upgrade.zip",
        f"{prefix}-source.zip",
        f"{prefix}-android-debug.apk",
        "release-manifest.json",
        "SHA256SUMS",
    }
    missing = sorted(name for name in required if not (directory / name).is_file())
    if missing:
        raise ReleaseError(f"missing release artifacts: {missing}")

    checksum_lines = (directory / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    checksums: dict[str, str] = {}
    for line in checksum_lines:
        try:
            digest, name = line.split("  ", 1)
        except ValueError as error:
            raise ReleaseError("invalid SHA256SUMS line") from error
        if name in checksums or len(digest) != 64:
            raise ReleaseError("invalid or duplicate SHA256SUMS entry")
        checksums[name] = digest
    expected_checksummed = required - {"SHA256SUMS"}
    if set(checksums) != expected_checksummed:
        raise ReleaseError("SHA256SUMS artifact set mismatch")
    for name, expected in checksums.items():
        if sha256_path(directory / name) != expected:
            raise ReleaseError(f"checksum mismatch: {name}")

    manifest = json.loads((directory / "release-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or manifest.get("project") != "comptext-phone-agent" or manifest.get("version") != version:
        raise ReleaseError("release manifest identity mismatch")
    git_commit = manifest.get("git_commit")
    if not isinstance(git_commit, str) or len(git_commit) != 40 or any(char not in "0123456789abcdef" for char in git_commit):
        raise ReleaseError("release manifest git_commit is invalid")
    release_commit = f"{git_commit}\n".encode("ascii")

    artifacts = manifest.get("artifacts")
    expected_payloads = required - {"SHA256SUMS", "release-manifest.json"}
    if not isinstance(artifacts, dict) or set(artifacts) != expected_payloads:
        raise ReleaseError("release manifest artifact set mismatch")

    archive_sets: list[frozenset[str]] = []
    for kind in ("full", "upgrade", "source"):
        name = f"{prefix}-{kind}.zip"
        record = artifacts[name]
        if record.get("sha256") != sha256_path(directory / name) or record.get("size") != (directory / name).stat().st_size:
            raise ReleaseError(f"manifest mismatch: {name}")
        expected_members = {"RELEASE_COMMIT.txt": release_commit} if kind == "full" else None
        members = verify_zip(directory / name, prefix, expected_members=expected_members)
        manifest_files = record.get("files")
        expected_files = [{"path": path, "sha256": members[path]} for path in sorted(members)]
        if manifest_files != expected_files:
            raise ReleaseError(f"manifest file inventory mismatch: {name}")
        archive_sets.append(frozenset(members))
    if len(set(archive_sets)) != 3:
        raise ReleaseError("release archive profiles are not distinct")

    apk_name = f"{prefix}-android-debug.apk"
    apk_record = artifacts[apk_name]
    if apk_record.get("sha256") != sha256_path(directory / apk_name) or apk_record.get("size") != (directory / apk_name).stat().st_size:
        raise ReleaseError("manifest mismatch: Android APK")
    return {
        "version": version,
        "artifacts": sorted(required),
        "checksums": checksums,
        "archive_file_counts": [len(items) for items in archive_sets],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify CompText Phone Agent release artifacts")
    parser.add_argument("--directory", type=Path, default=Path(".dist"))
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        result = verify_release(args.directory.resolve(), args.version)
    except (OSError, ValueError, json.JSONDecodeError, ReleaseError) as error:
        print(f"release verification failed: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
