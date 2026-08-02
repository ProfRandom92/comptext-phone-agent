from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from ..runtime.policy import ToolPolicy
from ..storage.analyzer import StorageAnalyzer
from ..storage.cleanup import CleanupPlanner
from ..storage.duplicates import DuplicateDetector

@dataclass(slots=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    risk: int = 0
    read_only: bool = True
    approval: str = "never"
    max_calls_per_run: int = 2
    storage_intensive: bool = False
    network_required: bool = False
    @property
    def policy(self) -> ToolPolicy:
        return ToolPolicy(self.name,self.risk,self.read_only,self.approval,self.max_calls_per_run,self.storage_intensive,self.network_required)
    def ollama_schema(self) -> dict[str, Any]:
        return {"type":"function","function":{"name":self.name,"description":self.description,"parameters":self.parameters}}

class ToolRegistry:
    def __init__(self, context, root: Path):
        self.context=context; self.root=root.resolve(); self._tools={}
        self._register_defaults()
    def register(self, spec: ToolSpec) -> None: self._tools[spec.name]=spec
    def schemas(self, safe_mode: bool=False) -> list[dict[str, Any]]:
        return [x.ollama_schema() for x in self._tools.values() if not safe_mode or (x.read_only and x.approval == "never")]
    def get(self, name: str) -> ToolSpec | None: return self._tools.get(name)
    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools: raise ValueError(f"tool not allowed: {name}")
        return self._tools[name].handler(arguments)
    def _scan(self): return self.context.scanner.scan(self.root)
    def _safe_file(self, item) -> dict[str, Any]:
        data=item.to_dict()
        data.pop("absolute_path",None)
        data.pop("atime",None)
        return data
    def _safe_wifi(self) -> dict[str, Any]:
        raw=self.context.device_client().wifi()
        allowed={"ssid","frequency_mhz","link_speed_mbps","rssi","ssid_hidden","supplicant_state"}
        return {key:value for key,value in raw.items() if key in allowed}
    def _register_defaults(self) -> None:
        noargs={"type":"object","properties":{},"additionalProperties":False}
        self.register(ToolSpec("scan_storage","Analyze storage without modifying files",{"type":"object","properties":{"top":{"type":"integer","minimum":1,"maximum":100}},"additionalProperties":False},self._scan_storage,0,True,"never",2,True))
        self.register(ToolSpec("find_duplicates","Find exact duplicate files without modifying files",{"type":"object","properties":{"verify":{"type":"boolean"}},"additionalProperties":False},self._duplicates,0,True,"never",2,True))
        self.register(ToolSpec("largest_files","List largest files without modifying files",{"type":"object","properties":{"top":{"type":"integer","minimum":1,"maximum":100}},"additionalProperties":False},self._largest,0,True,"never",2,True))
        self.register(ToolSpec("old_files","List files by mtime age without modifying files",{"type":"object","properties":{"days":{"type":"integer","minimum":1,"maximum":10000},"top":{"type":"integer","minimum":1,"maximum":100}},"additionalProperties":False},self._old,0,True,"never",2,True))
        self.register(ToolSpec("device_battery","Read Android battery status",noargs,lambda _: self.context.device_client().battery(),0,True,"never",3,False))
        self.register(ToolSpec("device_wifi","Read Android Wi-Fi status",noargs,lambda _: self._safe_wifi(),0,True,"never",3,False))
        self.register(ToolSpec("cleanup_plan","Create a reversible cleanup plan only; never apply it",{"type":"object","properties":{"old_days":{"type":"integer","minimum":1,"maximum":10000}},"additionalProperties":False},self._cleanup_plan,1,False,"never",1,True))
    def _scan_storage(self,a):
        r=self._scan(); top=int(a.get("top",30)); an=StorageAnalyzer(r)
        return {"root":r.root,"total_files":r.total_files,"total_size":r.total_size,"errors":r.errors,"largest":[self._safe_file(x) for x in an.largest_files(top)],"changed":False}
    def _duplicates(self,a):
        r=self._scan(); groups=DuplicateDetector(self.context.hash_cache).find(r,verify=bool(a.get("verify",True)))
        safe=[]
        for group in groups[:50]:
            data=group.to_dict()
            data["files"]=[str(Path(x).resolve().relative_to(self.root)) for x in group.files]
            data["protected"]=[str(Path(x).resolve().relative_to(self.root)) for x in group.protected]
            safe.append(data)
        return {"groups":safe,"group_count":len(groups),"truncated":len(groups)>50,"changed":False}
    def _largest(self,a):
        r=self._scan(); return {"files":[self._safe_file(x) for x in StorageAnalyzer(r).largest_files(int(a.get("top",30)))],"changed":False}
    def _old(self,a):
        r=self._scan(); return {"files":[self._safe_file(x) for x in StorageAnalyzer(r).old_files(int(a.get("days",365)),int(a.get("top",30)))],"age_basis":"mtime","changed":False}
    def _cleanup_plan(self,a):
        r=self._scan(); p=CleanupPlanner(self.context.exclusions).plan(r,session_id="chat",old_days=int(a.get("old_days",365))); self.context.approvals.save_plan(p)
        return {"plan":p.to_dict(),"changed":False,"approval_required":True}
