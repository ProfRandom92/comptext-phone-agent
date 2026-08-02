from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any
import uuid
import hashlib
from ..audit.database import Database
from .events import RuntimeEvent
from .signals import RunSignal, SignalType


@dataclass(frozen=True, slots=True)
class AgentRun:
    id: str
    session_id: str
    goal: str
    state: str
    stop_reason: str | None
    created_at: str
    updated_at: str
    error: str | None = None


class RuntimeStore:
    def __init__(self, database: Database):
        self.database = database

    def create_run(self, session_id: str, goal: str, state: str = "planning") -> AgentRun:
        run_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO agent_runs(id,session_id,goal,state,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (run_id, session_id, goal, state, now, now),
            )
        return AgentRun(run_id, session_id, goal, state, None, now, now)

    def load_run(self, run_id: str) -> AgentRun | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id,session_id,goal,state,stop_reason,created_at,updated_at,error FROM agent_runs WHERE id=?",
                (run_id,),
            ).fetchone()
        return AgentRun(**dict(row)) if row else None

    def update_run(self, run_id: str, *, state: str, stop_reason: str | None = None, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE agent_runs SET state=?,stop_reason=?,error=?,updated_at=? WHERE id=?",
                (state, stop_reason, error, now, run_id),
            )

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any] | None = None) -> RuntimeEvent:
        with self.database.connect() as connection:
            previous = connection.execute(
                "SELECT sequence,event_hash FROM agent_events WHERE run_id=? ORDER BY sequence DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            sequence = int(previous["sequence"]) + 1 if previous else 1
            parent = str(previous["event_hash"]) if previous else None
            event = RuntimeEvent.create(
                run_id=run_id,
                sequence=sequence,
                event_type=event_type,
                payload=payload or {},
                parent_event_hash=parent,
            )
            connection.execute(
                "INSERT INTO agent_events(id,run_id,sequence,event_type,timestamp,payload,parent_event_hash,event_hash,schema_version) VALUES(?,?,?,?,?,?,?,?,?)",
                (event.id, event.run_id, event.sequence, event.event_type, event.timestamp,
                 json.dumps(event.payload, ensure_ascii=False, sort_keys=True), event.parent_event_hash,
                 event.event_hash, event.version),
            )
        return event

    def list_events(self, run_id: str, after_sequence: int = 0) -> list[RuntimeEvent]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id,run_id,sequence,event_type,timestamp,payload,parent_event_hash,event_hash,schema_version FROM agent_events WHERE run_id=? AND sequence>? ORDER BY sequence",
                (run_id, after_sequence),
            ).fetchall()
        return [
            RuntimeEvent(
                id=row["id"], run_id=row["run_id"], sequence=row["sequence"],
                event_type=row["event_type"], timestamp=row["timestamp"],
                payload=json.loads(row["payload"]), parent_event_hash=row["parent_event_hash"],
                event_hash=row["event_hash"], version=row["schema_version"],
            ) for row in rows
        ]

    def append_signal(self, run_id: str, signal_type: SignalType, payload: dict[str, Any] | None=None) -> RunSignal:
        now=datetime.now(timezone.utc).isoformat()
        with self.database.connect() as connection:
            cursor=connection.execute(
                "INSERT INTO agent_signals(run_id,signal_type,payload,created_at) VALUES(?,?,?,?)",
                (run_id,signal_type.value,json.dumps(payload or {},ensure_ascii=False,sort_keys=True),now),
            )
            signal_id=int(cursor.lastrowid)
        return RunSignal(signal_id,run_id,signal_type,payload or {},now,None)

    def list_signals(self, run_id: str, *, unconsumed_only: bool=False) -> list[RunSignal]:
        query="SELECT id,run_id,signal_type,payload,created_at,consumed_at FROM agent_signals WHERE run_id=?"
        if unconsumed_only: query+=" AND consumed_at IS NULL"
        query+=" ORDER BY id"
        with self.database.connect() as connection:
            rows=connection.execute(query,(run_id,)).fetchall()
        return [RunSignal(row['id'],row['run_id'],SignalType(row['signal_type']),json.loads(row['payload']),row['created_at'],row['consumed_at']) for row in rows]

    def consume_signal(self, run_id: str, signal_type: SignalType) -> RunSignal | None:
        now=datetime.now(timezone.utc).isoformat()
        with self.database.connect() as connection:
            row=connection.execute(
                "SELECT id,run_id,signal_type,payload,created_at,consumed_at FROM agent_signals WHERE run_id=? AND signal_type=? AND consumed_at IS NULL ORDER BY id LIMIT 1",
                (run_id,signal_type.value),
            ).fetchone()
            if not row: return None
            connection.execute("UPDATE agent_signals SET consumed_at=? WHERE id=?",(now,row['id']))
        return RunSignal(row['id'],row['run_id'],SignalType(row['signal_type']),json.loads(row['payload']),row['created_at'],now)

    @staticmethod
    def tool_idempotency_key(run_id: str, call_id: str, name: str, arguments: dict[str, Any]) -> str:
        body=json.dumps({'run_id':run_id,'call_id':call_id,'name':name,'arguments':arguments},sort_keys=True,separators=(',',':'),default=str)
        return hashlib.sha256(body.encode('utf-8')).hexdigest()

    def load_tool_result(self, key: str) -> Any | None:
        with self.database.connect() as connection:
            row=connection.execute("SELECT result FROM tool_executions WHERE idempotency_key=?",(key,)).fetchone()
        return json.loads(row['result']) if row else None

    def save_tool_result(self, key: str, run_id: str, call_id: str, name: str, result: Any) -> None:
        now=datetime.now(timezone.utc).isoformat()
        with self.database.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO tool_executions(idempotency_key,run_id,call_id,tool_name,result,created_at) VALUES(?,?,?,?,?,?)",
                (key,run_id,call_id,name,json.dumps(result,ensure_ascii=False,sort_keys=True,default=str),now),
            )

