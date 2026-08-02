from __future__ import annotations
from dataclasses import dataclass
from typing import Any

TRUSTED_ACTIONS = (
    'scan_storage',
    'find_duplicates',
    'largest_files',
    'old_files',
    'device_battery',
    'device_wifi',
    'cleanup_plan',
)

@dataclass(frozen=True, slots=True)
class ActionDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    risk: int
    read_only: bool
    approval: str

class ActionCatalog:
    def __init__(self, actions: dict[str,ActionDefinition]): self._actions=dict(actions)
    @classmethod
    def from_registry(cls, registry) -> 'ActionCatalog':
        actions={}
        missing=[name for name in TRUSTED_ACTIONS if name not in registry._tools]
        if missing:
            raise RuntimeError(f'missing trusted actions: {missing}')
        for name in TRUSTED_ACTIONS:
            spec=registry._tools[name]
            actions[name]=ActionDefinition(name,spec.description,spec.parameters,spec.risk,spec.read_only,spec.approval)
        return cls(actions)
    def get(self,name:str) -> ActionDefinition | None: return self._actions.get(name)
    def names(self) -> tuple[str,...]: return tuple(sorted(self._actions))
    def schemas(self) -> list[dict[str,Any]]:
        return [{'name':x.name,'description':x.description,'parameters':x.parameters} for x in self._actions.values()]
