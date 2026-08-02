from __future__ import annotations
from pathlib import Path
import sqlite3, time

class HashCache:
    def __init__(self, database_path: Path):
        self.database_path = database_path
    def get(self, path: Path, kind: str) -> str | None:
        stat = path.stat()
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT digest FROM file_hash_cache WHERE path=? AND size=? AND mtime_ns=? AND kind=?",
                (str(path.resolve()), stat.st_size, stat.st_mtime_ns, kind),
            ).fetchone()
        return str(row[0]) if row else None
    def put(self, path: Path, kind: str, digest: str) -> None:
        stat = path.stat()
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO file_hash_cache(path,size,mtime_ns,kind,digest,updated_at) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(path,kind) DO UPDATE SET size=excluded.size,mtime_ns=excluded.mtime_ns,digest=excluded.digest,updated_at=excluded.updated_at",
                (str(path.resolve()), stat.st_size, stat.st_mtime_ns, kind, digest, int(time.time())),
            )
    def prune_missing(self) -> int:
        with sqlite3.connect(self.database_path) as connection:
            rows = connection.execute("SELECT path,kind FROM file_hash_cache").fetchall()
            missing=[(p,k) for p,k in rows if not Path(p).exists()]
            connection.executemany("DELETE FROM file_hash_cache WHERE path=? AND kind=?", missing)
        return len(missing)
