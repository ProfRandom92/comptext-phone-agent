from __future__ import annotations
from typing import Any
from .models import ToolCardView
from .projection import tool_card_from_event

_ALLOWED = {'tool.started.v1','tool.completed.v1','tool.failed.v1','approval.requested.v1','run.failed.v1'}

def card_from_event(event: Any) -> ToolCardView:
    event_type=getattr(event,'event_type',None) or event.get('event_type','unknown')
    payload=getattr(event,'payload',None) or event.get('payload',{})
    if event_type=='approval.requested.v1':
        return ToolCardView('approval',str(payload.get('tool','Freigabe')),'waiting_approval','Freigabe erforderlich',approval_id=str(payload.get('approval_id','')),call_id=str(payload.get('call_id') or payload.get('approval_id','')))
    if event_type=='run.failed.v1':
        return ToolCardView('error','Agentenlauf','failed',str(payload.get('reason') or payload.get('error') or 'Fehler'))
    if event_type not in _ALLOWED:
        return ToolCardView('generic','Ereignis','unknown',event_type)
    return tool_card_from_event(event_type,payload)
