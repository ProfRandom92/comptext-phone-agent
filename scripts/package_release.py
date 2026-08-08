#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tomllib
import zipfile


ARCHIVE_KINDS = ("full", "upgrade", "source")
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
ROOT_METADATA = {
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "install-termux.sh",
    "pyproject.toml",
    "uninstall.sh",
    "update.sh",
}
SOURCE_PREFIXES = ("android-broker/", "config/", "scripts/", "src/", "templates/", "tests/")
UPGRADE_PREFIXES = ("config/", "scripts/", "src/", "templates/")
FORBIDDEN_PARTS = {".git", ".gradle", ".idea", ".venv", "__pycache__", "build", "dist", "node_modules"}
FORBIDDEN_SUFFIXES = {
    ".aab", ".apk", ".db", ".gguf", ".jks", ".keystore", ".litertlm",
    ".onnx", ".p12", ".pem", ".pfx", ".pyc", ".pyo", ".safetensors",
    ".sqlite", ".sqlite3", ".tflite",
}


class ReleaseError(RuntimeError):
    pass


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_release_files(kind: str, paths: set[str]) -> set[str]:
    if kind == "full":
        return set(paths)
    if kind == "source":
        return {path for path in paths if path in ROOT_METADATA or path.startswith(SOURCE_PREFIXES)}
    if kind == "upgrade":
        return {path for path in paths if path in ROOT_METADATA or path.startswith(UPGRADE_PREFIXES)}
    raise ReleaseError(f"unknown archive kind: {kind}")


def _forbidden_member(path: PurePosixPath) -> bool:
    lowered = {part.casefold() for part in path.parts}
    name = path.name.casefold()
    return bool(
        lowered & FORBIDDEN_PARTS
        or path.suffix.casefold() in FORBIDDEN_SUFFIXES
        or name == "local.properties"
        or name == ".env"
        or (name.startswith(".env.") and not name.endswith((".example", ".sample", ".template")))
    )


def _validate_relative_path(value: str) -> PurePosixPath:
    if "\\" in value:
        raise ReleaseError(f"unsafe archive path: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ReleaseError(f"unsafe archive path: {value}")
    return path


def write_deterministic_zip(
    root: Path,
    destination: Path,
    files: set[str] | list[str],
    modes: dict[str, int],
    prefix: str,
    overrides: dict[str, bytes] | None = None,
) -> None:
    prefix_path = _validate_relative_path(prefix)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(files):
            path = _validate_relative_path(relative)
            if _forbidden_member(path):
                raise ReleaseError(f"forbidden release file: {relative}")
            absolute = root / Path(*path.parts)
            if not absolute.is_file() or absolute.is_symlink():
                raise ReleaseError(f"release file is missing, non-regular, or a symlink: {relative}")
            name = (prefix_path / path).as_posix()
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.create_system = 3
            mode = modes.get(relative, 0o644)
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            data = overrides[relative] if overrides and relative in overrides else absolute.read_bytes()
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_zip(
    path: Path,
    expected_prefix: str,
    expected_members: dict[str, bytes] | None = None,
) -> dict[str, str]:
    prefix = _validate_relative_path(expected_prefix).as_posix() + "/"
    hashes: dict[str, str] = {}
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ReleaseError(f"ZIP CRC failed: {path.name}")
            for item in archive.infolist():
                name = item.filename
                member = _validate_relative_path(name)
                if not name.startswith(prefix):
                    raise ReleaseError(f"unsafe archive path: {name}")
                relative = PurePosixPath(*member.parts[1:])
                if not relative.parts or _forbidden_member(relative):
                    raise ReleaseError(f"forbidden archive member: {name}")
                if name in hashes:
                    raise ReleaseError(f"duplicate archive member: {name}")
                data = archive.read(item)
                relative_name = relative.as_posix()
                if expected_members and relative_name in expected_members and data != expected_members[relative_name]:
                    raise ReleaseError(f"release metadata mismatch: {relative_name}")
                hashes[name] = hashlib.sha256(data).hexdigest()
    except (OSError, zipfile.BadZipFile) as error:
        raise ReleaseError(f"invalid ZIP {path.name}: {error}") from error
    if not hashes:
        raise ReleaseError(f"empty ZIP: {path.name}")
    return hashes


def git_files(root: Path) -> tuple[set[str], dict[str, int]]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-s", "-z"],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ReleaseError(result.stderr.decode(errors="replace").strip() or "git ls-files failed")
    files: set[str] = set()
    modes: dict[str, int] = {}
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, encoded_path = raw.split(b"\t", 1)
        mode_text, _object_id, stage = metadata.split(b" ", 2)
        if stage != b"0":
            raise ReleaseError("unmerged Git index entry")
        relative = encoded_path.decode("utf-8", errors="surrogateescape")
        _validate_relative_path(relative)
        files.add(relative)
        modes[relative] = 0o755 if mode_text == b"100755" else 0o644
    return files, modes


def project_version(root: Path) -> str:
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    value = data.get("project", {}).get("version")
    if not isinstance(value, str) or not value:
        raise ReleaseError("pyproject project.version is missing")
    return value


def _git_value(root: Path, *arguments: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, text=True, check=False)
    if result.returncode:
        raise ReleaseError(result.stderr.strip() or "git metadata query failed")
    return result.stdout.strip()


def build_release(root: Path, output: Path, apk: Path, expected_version: str | None = None) -> list[Path]:
    root = root.resolve()
    output = output.resolve()
    version = project_version(root)
    if expected_version is not None and version != expected_version:
        raise ReleaseError(f"version mismatch: expected {expected_version}, found {version}")
    if not apk.is_file() or apk.suffix.casefold() != ".apk":
        raise ReleaseError("a built Android APK is required")
    tracked, modes = git_files(root)
    git_commit = _git_value(root, "rev-parse", "HEAD")
    if "RELEASE_COMMIT.txt" not in tracked:
        raise ReleaseError("tracked RELEASE_COMMIT.txt is required for full-archive provenance")
    release_commit = f"{git_commit}\n".encode("ascii")
    prefix = f"comptext-phone-agent-{version}"
    output.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, dict[str, object]] = {}
    written: list[Path] = []

    for kind in ARCHIVE_KINDS:
        selected = select_release_files(kind, tracked)
        if not selected:
            raise ReleaseError(f"archive profile is empty: {kind}")
        destination = output / f"{prefix}-{kind}.zip"
        overrides = {"RELEASE_COMMIT.txt": release_commit} if kind == "full" else None
        write_deterministic_zip(root, destination, selected, modes, prefix, overrides=overrides)
        expected_members = {"RELEASE_COMMIT.txt": release_commit} if kind == "full" else None
        members = verify_zip(destination, prefix, expected_members=expected_members)
        artifacts[destination.name] = {
            "kind": kind,
            "sha256": sha256_path(destination),
            "size": destination.stat().st_size,
            "files": [{"path": name, "sha256": members[name]} for name in sorted(members)],
        }
        written.append(destination)

    apk_destination = output / f"{prefix}-android-debug.apk"
    shutil.copyfile(apk, apk_destination)
    artifacts[apk_destination.name] = {
        "kind": "android-debug-apk",
        "sha256": sha256_path(apk_destination),
        "size": apk_destination.stat().st_size,
    }
    written.append(apk_destination)

    manifest_path = output / "release-manifest.json"
    manifest = {
        "schema": 1,
        "project": "comptext-phone-agent",
        "version": version,
        "git_commit": git_commit,
        "source_date": _git_value(root, "show", "-s", "--format=%cI", "HEAD"),
        "artifacts": {name: artifacts[name] for name in sorted(artifacts)},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    written.append(manifest_path)

    checksums_path = output / "SHA256SUMS"
    checksummed = sorted(written, key=lambda item: item.name)
    checksums_path.write_text(
        "".join(f"{sha256_path(item)}  {item.name}\n" for item in checksummed),
        encoding="ascii",
        newline="\n",
    )
    written.append(checksums_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Build verified CompText Phone Agent release artifacts")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path(".dist"))
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--version")
    args = parser.parse_args()
    try:
        written = build_release(args.root, args.output, args.apk, args.version)
    except (OSError, ReleaseError) as error:
        print(f"release packaging failed: {error}", file=os.sys.stderr)
        return 1
    for path in written:
        print(f"{sha256_path(path)}  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
