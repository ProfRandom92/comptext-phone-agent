from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


MAX_TRACKED_BYTES = 5 * 1024 * 1024
FORBIDDEN_DIRECTORIES = {
    ".gradle",
    ".idea",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
FORBIDDEN_SUFFIXES = {
    ".aab",
    ".apk",
    ".db",
    ".gguf",
    ".jks",
    ".keystore",
    ".litertlm",
    ".onnx",
    ".p12",
    ".pem",
    ".pfx",
    ".pyc",
    ".pyo",
    ".safetensors",
    ".sqlite",
    ".sqlite3",
    ".tflite",
}
BACKUP_PATTERN = re.compile(
    r"(?:\.before(?:[-_.].*)?|\.bak|\.backup|\.orig|\.old|\.tmp|\.swp|~)$",
    re.IGNORECASE,
)
SECRET_PATTERNS = {
    "aws access key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "github token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    "gitlab token": re.compile(rb"glpat-[A-Za-z0-9_-]{20,}"),
    "google api key": re.compile(rb"AIza[0-9A-Za-z_-]{35}"),
    "npm token": re.compile(rb"npm_[A-Za-z0-9]{30,}"),
    "openai key": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "pypi token": re.compile(rb"pypi-[A-Za-z0-9_-]{40,}"),
    "slack token": re.compile(rb"xox[baprs]-[A-Za-z0-9-]{20,}"),
    "private key": re.compile(rb"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
}


@dataclass(frozen=True, slots=True)
class Finding:
    path: str
    reason: str


def tracked_paths(root: Path, *, staged: bool) -> list[str]:
    command = ["git", "-C", str(root)]
    if staged:
        command.extend(
            ["diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"]
        )
    else:
        command.extend(["ls-files", "-z"])
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or "git tracked-file query failed")
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    ]


def path_reason(relative_path: str) -> str | None:
    normalized = PurePosixPath(relative_path.replace("\\", "/"))
    lowered_parts = {part.casefold() for part in normalized.parts}
    blocked_directory = lowered_parts & FORBIDDEN_DIRECTORIES
    if blocked_directory:
        return f"generated directory: {sorted(blocked_directory)[0]}"

    name = normalized.name.casefold()
    if name == "local.properties":
        return "local SDK path file"
    if name == ".env" or (
        name.startswith(".env.")
        and not name.endswith((".example", ".sample", ".template"))
    ):
        return "environment secret file"
    if normalized.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return f"forbidden artifact type: {normalized.suffix.casefold()}"
    if BACKUP_PATTERN.search(normalized.name):
        return "backup or temporary file"
    return None


def scan(root: Path, relative_paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for relative_path in relative_paths:
        reason = path_reason(relative_path)
        absolute_path = root / Path(relative_path)
        if reason is not None:
            findings.append(Finding(relative_path, reason))
            continue
        if not absolute_path.is_file():
            continue
        size = absolute_path.stat().st_size
        if size > MAX_TRACKED_BYTES:
            findings.append(
                Finding(relative_path, f"file exceeds {MAX_TRACKED_BYTES} bytes")
            )
            continue
        data = absolute_path.read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(data):
                findings.append(Finding(relative_path, f"possible {label}"))
                break
    return sorted(findings, key=lambda finding: (finding.path, finding.reason))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    try:
        paths = tracked_paths(root, staged=args.staged)
        findings = scan(root, paths)
    except (OSError, RuntimeError) as error:
        print(f"tracked-file guard error: {error}", file=sys.stderr)
        return 2

    if findings:
        for finding in findings:
            print(f"forbidden tracked file: {finding.path} ({finding.reason})", file=sys.stderr)
        return 1

    print("tracked-file guard: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
