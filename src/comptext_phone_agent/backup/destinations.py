from __future__ import annotations
from dataclasses import dataclass

@dataclass(slots=True)
class BackupDestination:
    name: str
    target: str
    kind: str = "rclone"

def parse_destination(value: str) -> BackupDestination:
    if ":" not in value:
        return BackupDestination("local", value, "local")
    remote = value.split(":", 1)[0]
    return BackupDestination(remote, value, "rclone")
