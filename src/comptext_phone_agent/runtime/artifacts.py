from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, json, uuid
from pathlib import Path
from typing import Any
from ..audit.database import Database

SENSITIVE_WIFI={"bssid","mac_address","ip","network_id"}

@dataclass(frozen=True,slots=True)
class Artifact:
    id:str; run_id:str; kind:str; media_type:str; sha256:str; payload:Any; created_at:str

class ArtifactStore:
    def __init__(self,database:Database,storage_root:Path): self.database=database; self.storage_root=storage_root.resolve()
    def put(self,run_id:str,kind:str,payload:Any,media_type:str="application/json") -> Artifact:
        raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,default=str)
        item=Artifact(str(uuid.uuid4()),run_id,kind,media_type,hashlib.sha256(raw.encode()).hexdigest(),payload,datetime.now(timezone.utc).isoformat())
        with self.database.connect() as c:
            c.execute("INSERT INTO agent_artifacts(id,run_id,kind,media_type,sha256,payload,created_at) VALUES(?,?,?,?,?,?,?)",(item.id,item.run_id,item.kind,item.media_type,item.sha256,raw,item.created_at))
        return item
    def project_for_model(self,payload:Any,max_items:int=50) -> Any:
        def clean(value:Any,key:str|None=None):
            if key in SENSITIVE_WIFI: return None
            if isinstance(value,dict):
                return {k:v2 for k,v in value.items() if (v2:=clean(v,k)) is not None and k not in {"absolute_path","atime"}}
            if isinstance(value,list): return [clean(x) for x in value[:max_items]]
            if isinstance(value,str) and value.startswith('/'):
                try: return str(Path(value).resolve().relative_to(self.storage_root))
                except (ValueError,OSError): return "<redacted-path>"
            return value
        return clean(payload)
