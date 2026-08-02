from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import os, shutil, subprocess, tempfile, time
from ..models import ActionPlan
from ..storage.exclusions import ExclusionEngine
from ..storage.scanner import sha256_file
from .destinations import parse_destination

class RcloneError(RuntimeError):
    pass

@dataclass(slots=True)
class RcloneResult:
    dry_run: bool
    command_preview: list[str]
    stdout: str
    stderr: str
    returncode: int
    copied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    verified: list[str] = field(default_factory=list)

class RcloneClient:
    def __init__(self, binary: str = "rclone", timeout_seconds: int = 900, exclusions: ExclusionEngine | None = None, retries: int = 2, conflict_strategy: str = "skip"):
        self.binary = binary
        self.timeout_seconds = timeout_seconds
        self.exclusions = exclusions
        self.retries = max(0, retries)
        if conflict_strategy not in {"skip", "rename"}:
            raise ValueError("conflict_strategy must be skip or rename")
        self.conflict_strategy = conflict_strategy
    def apply(self, plan: ActionPlan, dry_run: bool = True) -> RcloneResult:
        if any(action.action != "upload" for action in plan.actions):
            raise RcloneError("backup plan contains unsupported actions")
        for action in plan.actions:
            if self.exclusions:
                self.exclusions.assert_can_upload(action.source)
        if not plan.actions:
            return RcloneResult(dry_run, [], "", "", 0)
        destination = plan.actions[0].target or ""
        if any(action.target != destination for action in plan.actions):
            raise RcloneError("one plan must target exactly one destination")
        parsed = parse_destination(destination)
        if parsed.kind == "local":
            return self._apply_local(plan, Path(parsed.target).expanduser().resolve(), dry_run)
        return self._apply_rclone(plan, destination, dry_run)
    def _apply_local(self, plan: ActionPlan, target: Path, dry_run: bool) -> RcloneResult:
        preview = ["local-copy", "<approved-files>", str(target), f"--conflict={self.conflict_strategy}"]
        if dry_run:
            return RcloneResult(True, preview + ["--dry-run"], "", "", 0)
        target.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        skipped: list[str] = []
        verified: list[str] = []
        for action in plan.actions:
            source = Path(action.source).resolve()
            destination = target / source.name
            if destination.exists():
                if self.conflict_strategy == "skip":
                    skipped.append(str(destination)); continue
                index = 1
                while destination.exists():
                    destination = target / f"{source.stem}-copy-{index}{source.suffix}"
                    index += 1
            temporary = destination.with_suffix(destination.suffix + ".part")
            shutil.copy2(source, temporary)
            if sha256_file(source) != sha256_file(temporary):
                temporary.unlink(missing_ok=True)
                raise RcloneError(f"hash verification failed: {source}")
            os.replace(temporary, destination)
            copied.append(str(destination)); verified.append(str(destination))
        return RcloneResult(False, preview, "", "", 0, copied, skipped, verified)
    def _apply_rclone(self, plan: ActionPlan, destination: str, dry_run: bool) -> RcloneResult:
        sources = [Path(action.source).resolve() for action in plan.actions]
        common = Path(os.path.commonpath([str(source.parent) for source in sources])).resolve()
        relative = [str(source.relative_to(common)) for source in sources]
        preview = [self.binary, "copy", str(common), destination, "--files-from", "<temporary-list>", "--no-traverse", "--ignore-existing"]
        if dry_run:
            return RcloneResult(True, preview + ["--dry-run"], "", "", 0)
        if shutil.which(self.binary) is None:
            raise RcloneError("rclone is not installed")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write("\n".join(relative) + "\n")
            list_path = handle.name
        command = [self.binary, "copy", str(common), destination, "--files-from", list_path, "--no-traverse", "--ignore-existing"]
        try:
            last_error = ""
            for attempt in range(self.retries + 1):
                try:
                    completed = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout_seconds, check=False)
                except subprocess.TimeoutExpired as error:
                    last_error = "rclone timeout"
                    if attempt >= self.retries:
                        raise RcloneError(last_error) from error
                else:
                    if completed.returncode == 0:
                        return RcloneResult(False, command, completed.stdout, completed.stderr, 0)
                    last_error = completed.stderr.strip() or "rclone failed"
                    if attempt >= self.retries:
                        raise RcloneError(last_error)
                time.sleep(min(2 ** attempt, 5))
            raise RcloneError(last_error or "rclone failed")
        finally:
            Path(list_path).unlink(missing_ok=True)
