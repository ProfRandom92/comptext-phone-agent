from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import hashlib, os, shutil, uuid
from ..audit.database import Database
from ..audit.logger import AuditLogger
from ..paths import ensure_no_symlink_escape
from .exclusions import ExclusionEngine
from .scanner import sha256_file

class TrashManager:
    def __init__(self, trash_dir: Path, database: Database, exclusions: ExclusionEngine):
        self.trash_dir = trash_dir
        self.database = database
        self.exclusions = exclusions
        self.audit = AuditLogger(database)
        trash_dir.mkdir(parents=True, exist_ok=True)
    def move(self, source: Path, approval_id: str, allowed_root: Path) -> str:
        source = ensure_no_symlink_escape(source, allowed_root)
        self.exclusions.assert_can_modify(source, allowed_root)
        if not source.is_file():
            raise FileNotFoundError(source)
        item_id = str(uuid.uuid4())
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = self.trash_dir / f"{stamp}-{item_id}-{source.name}"
        if destination.exists():
            destination = self.trash_dir / f"{stamp}-{item_id}-{uuid.uuid4().hex[:8]}-{source.name}"
        size = source.stat().st_size
        digest = sha256_file(source)
        shutil.move(str(source), str(destination))
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO trash_items(id,original_path,trash_path,created_at,size,sha256,approval_id) VALUES(?,?,?,?,?,?,?)",
                (item_id, str(source), str(destination), datetime.now(timezone.utc).isoformat(), size, digest, approval_id),
            )
        self.audit.log(action="trash.move", tool="trash", paths=[str(source), str(destination)], approval_id=approval_id, file_count=1, byte_count=size)
        return item_id
    def list(self, include_inactive: bool = False) -> list[dict]:
        query = "SELECT * FROM trash_items" if include_inactive else "SELECT * FROM trash_items WHERE restored_at IS NULL AND purged_at IS NULL"
        with self.database.connect() as connection:
            return [dict(row) for row in connection.execute(query + " ORDER BY created_at DESC")]
    def restore(self, item_id: str, approval_id: str | None = None) -> Path:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM trash_items WHERE id=?", (item_id,)).fetchone()
        if not row or row["purged_at"] or row["restored_at"]:
            raise KeyError("active trash item not found")
        source = Path(row["trash_path"])
        destination = Path(row["original_path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            destination = destination.with_name(destination.stem + f"-restored-{item_id[:8]}" + destination.suffix)
        shutil.move(str(source), str(destination))
        with self.database.connect() as connection:
            connection.execute("UPDATE trash_items SET restored_at=? WHERE id=?", (datetime.now(timezone.utc).isoformat(), item_id))
        self.audit.log(action="trash.restore", tool="trash", paths=[str(source), str(destination)], approval_id=approval_id, file_count=1, byte_count=row["size"])
        return destination
    def purge(self, item_ids: list[str], approval_id: str) -> int:
        purged = 0
        with self.database.connect() as connection:
            rows = []
            for item_id in item_ids:
                row = connection.execute(
                    "SELECT * FROM trash_items WHERE id=? AND restored_at IS NULL AND purged_at IS NULL",
                    (item_id,),
                ).fetchone()
                if row is not None:
                    rows.append(row)
            for row in rows:
                path = Path(row["trash_path"])
                if path.exists():
                    path.unlink()
                connection.execute("UPDATE trash_items SET purged_at=? WHERE id=?", (datetime.now(timezone.utc).isoformat(), row["id"]))
                purged += 1
        self.audit.log(action="trash.purge", tool="trash", paths=[str(x) for x in item_ids], approval_id=approval_id, file_count=purged)
        return purged
