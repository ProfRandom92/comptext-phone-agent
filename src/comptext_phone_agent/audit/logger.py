from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import json
from .database import Database
from .redaction import redact

class AuditLogger:
    def __init__(self, database: Database):
        self.database = database
    def log(
        self, *, action: str, session_id: str = "", user_id: str = "local", mode: str = "analysis",
        tool: str = "", parameters: dict[str, Any] | None = None, paths: list[str] | None = None,
        plan_id: str | None = None, approval_id: str | None = None, result: str = "ok",
        error: str | None = None, duration_ms: int = 0, file_count: int = 0, byte_count: int = 0,
    ) -> int:
        values = (
            datetime.now(timezone.utc).isoformat(), session_id, user_id, mode, action, tool,
            json.dumps(redact(parameters or {}), ensure_ascii=False),
            json.dumps(redact(paths or []), ensure_ascii=False),
            plan_id, approval_id, result, redact(error) if error else None,
            duration_ms, file_count, byte_count,
        )
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO audit_events(ts,session_id,user_id,mode,action,tool,parameters,paths,plan_id,approval_id,result,error,duration_ms,file_count,byte_count) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                values,
            )
            return int(cursor.lastrowid)
    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (limit,))]
    def get(self, event_id: int) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM audit_events WHERE id=?", (event_id,)).fetchone()
            return dict(row) if row else None
