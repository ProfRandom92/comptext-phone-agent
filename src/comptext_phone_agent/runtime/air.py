from __future__ import annotations
from typing import Any
from .events import RuntimeEvent

_KIND_MAP={
    'run.started.v1':'run_started','run.completed.v1':'run_completed','run.failed.v1':'run_failed','run.cancelled.v1':'run_cancelled',
    'tool.proposed.v1':'tool_proposed','tool.started.v1':'tool_started','tool.completed.v1':'tool_completed','tool.failed.v1':'tool_failed',
    'approval.requested.v1':'approval_requested','approval.accepted.v1':'approval_accepted','approval.rejected.v1':'approval_rejected',
    'context.compacted.v1':'context_compacted',
}

def runtime_event_to_air(event:RuntimeEvent) -> dict[str,Any]:
    return {
        'schema':'comptext.air.evidence-event','version':1,'event_id':event.id,'run_id':event.run_id,
        'sequence':event.sequence,'type':_KIND_MAP.get(event.event_type,'runtime_event'),
        'runtime_event_type':event.event_type,'timestamp':event.timestamp,'payload':event.payload,
        'parent_event_hash':event.parent_event_hash,'event_hash':event.event_hash,
    }
