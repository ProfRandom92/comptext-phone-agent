from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolPolicy:
    name: str
    risk: int = 0
    read_only: bool = True
    approval: str = "never"
    max_calls_per_run: int = 2
    storage_intensive: bool = False
    network_required: bool = False


@dataclass(frozen=True, slots=True)
class PreparedToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]
    policy: ToolPolicy
    resource_key: str | None = None


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool = False
    reason: str = "allowed"


def _validate_schema(arguments: dict[str, Any], schema: dict[str, Any]) -> None:
    properties=schema.get("properties",{})
    required=set(schema.get("required",[]))
    missing=required-set(arguments)
    if missing: raise ValueError(f"missing tool arguments: {sorted(missing)}")
    if schema.get("additionalProperties") is False:
        unknown=set(arguments)-set(properties)
        if unknown: raise ValueError(f"unknown tool arguments: {sorted(unknown)}")
    for key,value in arguments.items():
        rule=properties.get(key,{})
        expected=rule.get("type")
        valid=(expected=="integer" and isinstance(value,int) and not isinstance(value,bool)) or (expected=="boolean" and isinstance(value,bool)) or (expected=="string" and isinstance(value,str)) or expected is None
        if not valid: raise ValueError(f"invalid type for tool argument: {key}")
        if isinstance(value,(int,float)):
            if "minimum" in rule and value<rule["minimum"]: raise ValueError(f"tool argument below minimum: {key}")
            if "maximum" in rule and value>rule["maximum"]: raise ValueError(f"tool argument above maximum: {key}")


class RuntimePolicy:
    def __init__(self, registry, storage_root: Path, safe_mode: bool = False):
        self.registry = registry
        self.storage_root = storage_root.expanduser().resolve()
        self.safe_mode = safe_mode

    def prepare(self, *, call_id: str, name: str, arguments: dict[str, Any]) -> PreparedToolCall:
        spec = self.registry.get(name)
        if spec is None:
            raise ValueError(f"tool not allowed: {name}")
        _validate_schema(arguments or {}, spec.parameters)
        policy = spec.policy
        if self.safe_mode and (not policy.read_only or policy.approval != "never"):
            raise ValueError(f"tool disabled in safe mode: {name}")
        normalized = dict(arguments or {})
        for key in ("path", "root", "source", "target"):
            if key not in normalized:
                continue
            candidate = Path(str(normalized[key])).expanduser()
            if not candidate.is_absolute():
                candidate = self.storage_root / candidate
            resolved = candidate.resolve()
            try:
                resolved.relative_to(self.storage_root)
            except ValueError as exc:
                raise ValueError(f"path outside storage root: {resolved}") from exc
            normalized[key] = str(resolved)
        resource = "storage:" + str(self.storage_root) if policy.storage_intensive else None
        return PreparedToolCall(call_id, name, normalized, policy, resource)

    def authorize(self, call: PreparedToolCall) -> PolicyDecision:
        if self.safe_mode and not call.policy.read_only:
            return PolicyDecision(False, reason="safe_mode")
        if call.policy.approval == "always":
            return PolicyDecision(False, requires_approval=True, reason="approval_required")
        return PolicyDecision(True)
