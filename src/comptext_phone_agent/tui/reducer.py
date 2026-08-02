from __future__ import annotations
from typing import Iterable
from .card_factory import card_from_event
from .models import AppViewState, TranscriptItem

def reduce_events(events: Iterable, initial: AppViewState | None=None) -> AppViewState:
    state=initial or AppViewState()
    items=list(state.items); running=state.running; stop=state.stop_reason; run_id=state.run_id
    for event in sorted(events,key=lambda e:getattr(e,'sequence',0)):
        et=event.event_type; payload=event.payload; run_id=event.run_id
        ts=event.timestamp[11:19] if len(event.timestamp)>=19 else event.timestamp
        if et=='run.started.v1':
            running=True; items.append(TranscriptItem('system','Agent','Lauf gestartet',ts))
        elif et=='model.completed.v1' and payload.get('content'):
            items.append(TranscriptItem('agent','◈ Agent',str(payload['content']),ts))
        elif et.startswith('tool.') or et in {'approval.requested.v1','run.failed.v1'}:
            card=card_from_event(event); items.append(TranscriptItem('tool',card.title,card.summary,ts,card))
        elif et=='run.completed.v1':
            running=False; stop='final_answer'; answer=str(payload.get('answer',''))
            if answer and not any(i.kind=='agent' and i.body==answer for i in items): items.append(TranscriptItem('agent','◈ Agent',answer,ts))
        elif et=='run.cancelled.v1':
            running=False; stop='cancelled'; items.append(TranscriptItem('system','Abgebrochen','Der Lauf wurde beendet.',ts))
    return AppViewState(state.session_id,run_id,state.status,tuple(items),running,stop)
