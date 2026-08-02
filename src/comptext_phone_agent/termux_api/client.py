from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import json, shutil, subprocess
from .commands import READ_COMMANDS, WRITE_COMMANDS

class TermuxApiError(RuntimeError):
    pass

@dataclass(slots=True)
class CommandResult:
    command: list[str]
    data: Any
    stdout: str
    stderr: str
    returncode: int

class TermuxApiClient:
    def __init__(self, timeout_seconds: int = 8):
        self.timeout_seconds = timeout_seconds
    def available(self, command: str) -> bool:
        return shutil.which(command) is not None
    def run(self, command: list[str], expect_json: bool = False, stdin: str | None = None) -> CommandResult:
        if not command or shutil.which(command[0]) is None:
            raise TermuxApiError(f"Termux:API command unavailable: {command[0] if command else '<empty>'}")
        try:
            completed = subprocess.run(command, input=stdin, text=True, capture_output=True, timeout=self.timeout_seconds, check=False)
        except subprocess.TimeoutExpired as error:
            raise TermuxApiError(f"Termux:API timeout: {command[0]}") from error
        if completed.returncode != 0:
            raise TermuxApiError(completed.stderr.strip() or f"{command[0]} failed with {completed.returncode}")
        data: Any = completed.stdout.strip()
        if expect_json:
            try:
                data = json.loads(completed.stdout)
            except json.JSONDecodeError as error:
                raise TermuxApiError(f"invalid JSON from {command[0]}") from error
        return CommandResult(command, data, completed.stdout, completed.stderr, completed.returncode)
    def battery(self) -> dict:
        return self.run(READ_COMMANDS["battery"], expect_json=True).data
    def wifi(self) -> dict:
        return self.run(READ_COMMANDS["wifi"], expect_json=True).data
    def volume(self) -> Any:
        return self.run(READ_COMMANDS["volume"], expect_json=True).data
    def clipboard_get(self) -> str:
        return self.run(["termux-clipboard-get"]).data
    def notify(self, title: str, content: str) -> None:
        self.run(WRITE_COMMANDS["notify"] + ["--title", title, "--content", content])
    def clipboard_set(self, value: str) -> None:
        self.run(WRITE_COMMANDS["clipboard_set"], stdin=value)
    def tts(self, value: str) -> None:
        self.run(WRITE_COMMANDS["tts"] + [value])
    def vibrate(self, duration_ms: int = 250) -> None:
        self.run(WRITE_COMMANDS["vibrate"] + ["-d", str(duration_ms)])
