from __future__ import annotations
from pathlib import Path
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events(
 id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, session_id TEXT, user_id TEXT,
 mode TEXT, action TEXT NOT NULL, tool TEXT, parameters TEXT, paths TEXT, plan_id TEXT,
 approval_id TEXT, result TEXT, error TEXT, duration_ms INTEGER, file_count INTEGER, byte_count INTEGER
);
CREATE TABLE IF NOT EXISTS approvals(
 id TEXT PRIMARY KEY, plan_hash TEXT NOT NULL, token_hash TEXT NOT NULL, created_at INTEGER NOT NULL,
 expires_at INTEGER NOT NULL, risk INTEGER NOT NULL, consumed_at INTEGER, revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS plans(id TEXT PRIMARY KEY, body TEXT NOT NULL, plan_hash TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS trash_items(
 id TEXT PRIMARY KEY, original_path TEXT NOT NULL, trash_path TEXT NOT NULL, created_at TEXT NOT NULL,
 size INTEGER NOT NULL, sha256 TEXT, approval_id TEXT, restored_at TEXT, purged_at TEXT
);

CREATE TABLE IF NOT EXISTS file_hash_cache(
 path TEXT NOT NULL, size INTEGER NOT NULL, mtime_ns INTEGER NOT NULL, kind TEXT NOT NULL,
 digest TEXT NOT NULL, updated_at INTEGER NOT NULL, PRIMARY KEY(path,kind)
);

CREATE TABLE IF NOT EXISTS agent_runs(
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL, goal TEXT NOT NULL, state TEXT NOT NULL,
 stop_reason TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, error TEXT
);
CREATE TABLE IF NOT EXISTS agent_events(
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL, sequence INTEGER NOT NULL, event_type TEXT NOT NULL,
 timestamp TEXT NOT NULL, payload TEXT NOT NULL, parent_event_hash TEXT, event_hash TEXT NOT NULL,
 schema_version INTEGER NOT NULL DEFAULT 1,
 UNIQUE(run_id,sequence), FOREIGN KEY(run_id) REFERENCES agent_runs(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_agent_events_run_sequence ON agent_events(run_id,sequence);

CREATE TABLE IF NOT EXISTS agent_signals(
 id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, signal_type TEXT NOT NULL,
 payload TEXT NOT NULL, created_at TEXT NOT NULL, consumed_at TEXT,
 FOREIGN KEY(run_id) REFERENCES agent_runs(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_agent_signals_run ON agent_signals(run_id,id);
CREATE TABLE IF NOT EXISTS tool_executions(
 idempotency_key TEXT PRIMARY KEY, run_id TEXT NOT NULL, call_id TEXT NOT NULL, tool_name TEXT NOT NULL,
 result TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(run_id) REFERENCES agent_runs(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS agent_artifacts(
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL, kind TEXT NOT NULL, media_type TEXT NOT NULL,
 sha256 TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(run_id) REFERENCES agent_runs(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS chat_sessions(
 id TEXT PRIMARY KEY, title TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_messages(
 id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, role TEXT NOT NULL,
 content TEXT NOT NULL, tool_name TEXT, tool_payload TEXT, created_at TEXT NOT NULL,
 FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);
"""

class Database:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()
    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection
    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            columns={row["name"] for row in connection.execute("PRAGMA table_info(chat_sessions)")}
            if "summary" not in columns:
                connection.execute("ALTER TABLE chat_sessions ADD COLUMN summary TEXT NOT NULL DEFAULT ''")
            if "summary_message_id" not in columns:
                connection.execute("ALTER TABLE chat_sessions ADD COLUMN summary_message_id INTEGER")
        try:
            self.path.chmod(0o600)
        except OSError:
            pass
