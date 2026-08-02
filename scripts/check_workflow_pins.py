#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


USES = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
FULL_SHA = re.compile(r"[0-9a-f]{40}\Z")


def scan_workflow(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    findings: list[str] = []
    for value in USES.findall(text):
        if value.startswith("./"):
            continue
        if "@" not in value or not FULL_SHA.fullmatch(value.rsplit("@", 1)[1]):
            findings.append(f"{path.as_posix()}: action is not pinned to a full SHA: {value}")
    if not re.search(r"(?m)^permissions:\s*(?:\{\s*contents:\s*read\s*\}|\n)", text):
        findings.append(f"{path.as_posix()}: top-level least-privilege permissions are missing")
    if re.search(r"(?m)^\s*permissions:\s*write-all\s*$", text):
        findings.append(f"{path.as_posix()}: write-all permissions are forbidden")
    return findings


def scan_workflows(root: Path) -> list[str]:
    directory = root / ".github" / "workflows"
    files = sorted((*directory.glob("*.yml"), *directory.glob("*.yaml")))
    if not files:
        return ["no GitHub workflows found"]
    return [finding for path in files for finding in scan_workflow(path)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    findings = scan_workflows(args.root.resolve())
    if findings:
        for finding in findings:
            print(finding)
        return 1
    print("workflow pin and permission guard: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
