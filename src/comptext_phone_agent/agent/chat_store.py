from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import json, uuid
from ..audit.database import Database

@dataclass(slots=True)
class ChatSession:
    id: str
    title: str
    provider: str
    model: str

class ChatStore:
    def __init__(self, database: Database): self.database=database
    def create(self, provider: str, model: str, title: str="New chat") -> ChatSession:
        sid=str(uuid.uuid4()); now=datetime.now(timezone.utc).isoformat()
        with self.database.connect() as c:
            c.execute("INSERT INTO chat_sessions(id,title,provider,model,created_at,updated_at) VALUES(?,?,?,?,?,?)",(sid,title,provider,model,now,now))
        return ChatSession(sid,title,provider,model)
    def latest(self, provider: str, model: str) -> ChatSession | None:
        with self.database.connect() as c:
            r=c.execute("SELECT id,title,provider,model FROM chat_sessions WHERE provider=? AND model=? ORDER BY updated_at DESC LIMIT 1",(provider,model)).fetchone()
        return ChatSession(**dict(r)) if r else None
    def add(self, session_id: str, role: str, content: str, tool_name: str|None=None, tool_payload: dict|None=None) -> None:
        now=datetime.now(timezone.utc).isoformat()
        with self.database.connect() as c:
            c.execute("INSERT INTO chat_messages(session_id,role,content,tool_name,tool_payload,created_at) VALUES(?,?,?,?,?,?)",(session_id,role,content,tool_name,json.dumps(tool_payload,ensure_ascii=False) if tool_payload is not None else None,now))
            c.execute("UPDATE chat_sessions SET updated_at=? WHERE id=?",(now,session_id))
    def messages(self, session_id: str, limit: int=40) -> list[dict]:
        with self.database.connect() as c:
            rows=c.execute("SELECT role,content,tool_name,tool_payload FROM chat_messages WHERE session_id=? ORDER BY id DESC LIMIT ?",(session_id,limit)).fetchall()
        out=[]
        for r in reversed(rows):
            item={"role":r["role"],"content":r["content"]}
            if r["tool_name"]: item["tool_name"]=r["tool_name"]
            if r["tool_payload"]: item["tool_payload"]=json.loads(r["tool_payload"])
            out.append(item)
        return out
    def clear(self, session_id: str) -> None:
        with self.database.connect() as c:
            c.execute("DELETE FROM chat_messages WHERE session_id=?",(session_id,))
            c.execute("UPDATE chat_sessions SET summary='',summary_message_id=NULL WHERE id=?",(session_id,))
    def summary(self, session_id: str) -> str:
        with self.database.connect() as c:
            row=c.execute("SELECT summary FROM chat_sessions WHERE id=?",(session_id,)).fetchone()
        return str(row["summary"] or "") if row else ""
    def set_summary(self, session_id: str, summary: str) -> None:
        with self.database.connect() as c:
            last=c.execute("SELECT MAX(id) AS value FROM chat_messages WHERE session_id=?",(session_id,)).fetchone()
            c.execute("UPDATE chat_sessions SET summary=?,summary_message_id=? WHERE id=?",(summary,last["value"] if last else None,session_id))
