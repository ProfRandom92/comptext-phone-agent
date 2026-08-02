from __future__ import annotations
import json, re
from .models import RouteDecision, RouteKind

MAX_ROUTER_RESPONSE_BYTES = 64 * 1024
_CALL_RE=re.compile(r'^call:([A-Za-z_][A-Za-z0-9_]*)\s*(\{.*\})$',re.DOTALL)
_ACTION_RE=re.compile(r'[a-z][a-z0-9_]*\Z',re.ASCII)
_ALLOWED_FIELDS={'kind','action','arguments','confidence','reason','source'}


def _extract_single_object(value: str) -> dict:
    decoder=json.JSONDecoder()
    objects=[]
    position=0
    while True:
        start=value.find('{',position)
        if start < 0:
            break
        try:
            candidate,end=decoder.raw_decode(value,start)
        except json.JSONDecodeError:
            position=start+1
            continue
        position=end
        if isinstance(candidate,dict):
            objects.append(candidate)
    if not objects:
        raise ValueError('invalid router output')
    if len(objects) != 1:
        raise ValueError('multiple router objects are not allowed')
    return objects[0]

def parse_router_output(text: str) -> RouteDecision:
    if not isinstance(text,str):
        raise ValueError('router output must be text')
    if len(text.encode('utf-8')) > MAX_ROUTER_RESPONSE_BYTES:
        raise ValueError('router output is too large')
    value=text.strip()
    if value.startswith('planner:'):
        return RouteDecision(RouteKind.DELEGATE,reason=value.split(':',1)[1].strip(),confidence=1.0)
    if value.startswith('clarify:'):
        return RouteDecision(RouteKind.CLARIFY,reason=value.split(':',1)[1].strip(),confidence=1.0)
    if value.startswith('reject:'):
        return RouteDecision(RouteKind.REJECT,reason=value.split(':',1)[1].strip(),confidence=1.0)
    match=_CALL_RE.fullmatch(value)
    if match:
        args=json.loads(match.group(2))
        if not isinstance(args,dict): raise ValueError('function arguments must be an object')
        return RouteDecision(RouteKind.DIRECT_ACTION,match.group(1),args,1.0,source='functiongemma')
    data=_extract_single_object(value)
    unknown=set(data)-_ALLOWED_FIELDS
    if unknown: raise ValueError(f'unknown router fields: {sorted(unknown)}')
    raw_kind=data.get('kind')
    if raw_kind == 'planner':
        raw_kind='delegate'
    try: kind=RouteKind(raw_kind)
    except ValueError as exc: raise ValueError('unknown route kind') from exc
    args=data.get('arguments',{})
    if not isinstance(args,dict): raise ValueError('arguments must be an object')
    confidence=data.get('confidence',0.0)
    if isinstance(confidence,bool) or not isinstance(confidence,(int,float)):
        raise ValueError('confidence must be a number')
    action=data.get('action')
    if kind is RouteKind.DIRECT_ACTION and (not isinstance(action,str) or not _ACTION_RE.fullmatch(action)):
        raise ValueError('direct action requires a canonical action name')
    reason=data.get('reason','')
    source=data.get('source','router')
    if not isinstance(reason,str) or not isinstance(source,str):
        raise ValueError('reason and source must be strings')
    return RouteDecision(kind,action,args,confidence,reason,source)
