from __future__ import annotations
from ..models import OperatingMode, RiskClass

class PolicyError(PermissionError):
    pass

def require_mode(mode: OperatingMode, risk: RiskClass) -> None:
    if risk == RiskClass.READ_ONLY:
        return
    if mode == OperatingMode.ANALYSIS:
        raise PolicyError("analysis mode forbids modifications")
    if risk >= RiskClass.EXTERNAL_OR_BATCH and mode != OperatingMode.CONTROLLED:
        raise PolicyError("controlled mode required")

def confirmation_phrase(risk: RiskClass) -> str:
    return "DELETE PERMANENTLY" if risk == RiskClass.IRREVERSIBLE else "APPROVE"
