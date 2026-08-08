from __future__ import annotations
from pathlib import Path
from typing import Literal
import json
from pydantic import BaseModel, Field, ValidationError
from .providers import AgentProvider, ProviderError
from .prompts import SYSTEM_POLICY
from ..paths import normalize_path

class Intent(BaseModel):
    intent: Literal["scan","duplicates","cleanup_plan"]
    path: str | None = None
    top: int = Field(default=30, ge=1, le=1000)
    old_days: int = Field(default=365, ge=1, le=10000)

class ProviderBackedPlanner:
    def __init__(self, provider: AgentProvider): self.provider=provider
    def interpret(self, text: str, root: Path) -> dict:
        prompt=(SYSTEM_POLICY+"\nReturn JSON only with intent scan, duplicates, or cleanup_plan; optional path/top/old_days. "
                "Never return apply, shell, delete, move, upload, or arbitrary commands.")
        raw=self.provider.complete([{"role":"system","content":prompt},{"role":"user","content":text}]).strip()
        if raw.startswith('```'): raw='\n'.join(raw.splitlines()[1:-1])
        try: intent=Intent.model_validate(json.loads(raw))
        except (json.JSONDecodeError,ValidationError) as error: raise ProviderError(f"invalid typed provider response: {error}") from error
        path=normalize_path(intent.path or root,allowed_roots=[root],must_exist=True)
        return {"intent":intent.intent,"path":str(path),"top":intent.top,"old_days":intent.old_days,"plan_only":intent.intent=="cleanup_plan"}
