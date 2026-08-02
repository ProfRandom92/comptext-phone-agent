from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any
import uuid


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    id: str
    run_id: str
    sequence: int
    event_type: str
    timestamp: str
    payload: dict[str, Any]
    parent_event_hash: str | None
    event_hash: str
    schema: str = "comptext.runtime.event"
    version: int = 1

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        sequence: int,
        event_type: str,
        payload: dict[str, Any] | None = None,
        parent_event_hash: str | None = None,
        event_id: str | None = None,
        timestamp: str | None = None,
    ) -> "RuntimeEvent":
        eid = event_id or str(uuid.uuid4())
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        body = {
            "schema": "comptext.runtime.event",
            "version": 1,
            "id": eid,
            "run_id": run_id,
            "sequence": sequence,
            "event_type": event_type,
            "timestamp": ts,
            "payload": payload or {},
            "parent_event_hash": parent_event_hash,
        }
        digest = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
        return cls(event_hash=digest, **body)

    def verify(self) -> bool:
        body = {
            "schema": self.schema,
            "version": self.version,
            "id": self.id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "parent_event_hash": self.parent_event_hash,
        }
        return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest() == self.event_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "id": self.id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "parent_event_hash": self.parent_event_hash,
            "event_hash": self.event_hash,
        }
