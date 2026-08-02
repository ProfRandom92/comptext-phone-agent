from __future__ import annotations
import json, re
from .models import RouteDecision, RouteKind

_CALL_RE=re.compile(r'^call:([A-Za-z_][A-Za-z0-9_]*)\s*(\{.*\})$',re.DOTALL)

def parse_router_output(text: str) -> RouteDecision:
    value=text.strip()
    if value.startswith('planner:'):
        return RouteDecision(RouteKind.PLANNER,reason=value.split(':',1)[1].strip(),confidence=1.0)
    if value.startswith('clarify:'):
        return RouteDecision(RouteKind.CLARIFY,reason=value.split(':',1)[1].strip(),confidence=1.0)
    if value.startswith('reject:'):
        return RouteDecision(RouteKind.REJECT,reason=value.split(':',1)[1].strip(),confidence=1.0)
    match=_CALL_RE.fullmatch(value)
    if match:
        args=json.loads(match.group(2))
        if not isinstance(args,dict): raise ValueError('function arguments must be an object')
        return RouteDecision(RouteKind.DIRECT_ACTION,match.group(1),args,1.0,source='functiongemma')
    try:
        data=json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError('invalid router output') from exc
    if not isinstance(data,dict): raise ValueError('router output must be an object')
    try: kind=RouteKind(str(data.get('kind')))
    except ValueError as exc: raise ValueError('unknown route kind') from exc
    args=data.get('arguments') or {}
    if not isinstance(args,dict): raise ValueError('arguments must be an object')
    confidence=float(data.get('confidence',0.0))
    if not 0.0 <= confidence <= 1.0: raise ValueError('confidence must be between 0 and 1')
    action=data.get('action')
    if kind is RouteKind.DIRECT_ACTION and not isinstance(action,str): raise ValueError('direct action requires action')
    return RouteDecision(kind,action,args,confidence,str(data.get('reason','')),str(data.get('source','router')))
