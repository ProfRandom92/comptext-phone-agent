from __future__ import annotations
from dataclasses import dataclass
import json
from typing import Any

@dataclass(frozen=True,slots=True)
class CompactionResult:
    messages:list[dict[str,Any]]; compacted:bool; summary:str

class ContextCompactor:
    def __init__(self,max_messages:int=24,tail_messages:int=10,max_tool_bytes:int=30*1024):
        self.max_messages=max_messages; self.tail_messages=tail_messages; self.max_tool_bytes=max_tool_bytes
    def should_compact(self,messages:list[dict[str,Any]]) -> bool:
        tool_bytes=sum(len(json.dumps(m,ensure_ascii=False,default=str).encode()) for m in messages if m.get('role')=='tool')
        return len(messages)>self.max_messages or tool_bytes>self.max_tool_bytes
    def build_context(self,messages:list[dict[str,Any]],existing_summary:str="") -> CompactionResult:
        if not self.should_compact(messages): return CompactionResult(list(messages),False,existing_summary)
        protected=[]
        for m in messages[:-self.tail_messages]:
            text=str(m.get('content',''))
            if m.get('approval_required') or 'approval' in text.lower() or 'plan_id' in text:
                protected.append(m)
        older=messages[:-self.tail_messages]
        facts=[]
        for m in older:
            if m in protected: continue
            content=str(m.get('content','')).strip().replace('\n',' ')
            if content: facts.append(f"{m.get('role','unknown')}: {content[:240]}")
        summary=(existing_summary+'\n' if existing_summary else '')+' | '.join(facts[-12:])
        compacted=[{'role':'system','content':'SESSION_SUMMARY: '+summary.strip()},*protected,*messages[-self.tail_messages:]]
        return CompactionResult(compacted,True,summary.strip())
