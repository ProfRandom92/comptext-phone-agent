from __future__ import annotations
from typing import Any
from .models import LayoutMode, ToolCardView, layout_mode

def _fmt_bytes(value: Any) -> str:
    try:
        size=float(value)
    except (TypeError,ValueError):
        return str(value)
    for unit in ("B","KB","MB","GB","TB"):
        if abs(size)<1024 or unit=="TB":
            return f"{size:.1f} {unit}" if unit!="B" else f"{int(size)} B"
        size/=1024
    return str(value)

def tool_card_from_event(event_type:str,payload:dict[str,Any]) -> ToolCardView:
    name=str(payload.get('name') or payload.get('tool') or 'Werkzeug')
    call_id=str(payload.get('call_id',''))
    if event_type=='tool.started.v1':
        return ToolCardView('generic',name,'running','Wird ausgeführt …',progress=10,call_id=call_id)
    if event_type=='tool.failed.v1':
        return ToolCardView('error',name,'failed','Ausführung fehlgeschlagen',call_id=call_id)
    result=payload.get('result') or {}
    changed=bool(result.get('changed',False)) if isinstance(result,dict) else False
    protected=bool(result.get('protected') or result.get('protected_groups')) if isinstance(result,dict) else False
    kind='generic'; details=[]; summary='Abgeschlossen'
    if name=='scan_storage' and isinstance(result,dict):
        kind='storage'
        total=result.get('total_files',0); size=result.get('total_size')
        summary=f"{total} Dateien geprüft"
        details=[('Gesamt',_fmt_bytes(size))] if size is not None else []
    elif name=='find_duplicates' and isinstance(result,dict):
        kind='duplicates'; groups=result.get('group_count',len(result.get('groups',[])) if isinstance(result.get('groups'),list) else 0)
        summary=f"{groups} Gruppen gefunden"
        details=[('Gruppen',str(groups))]
    elif isinstance(result,dict):
        count=result.get('group_count',result.get('total_files',len(result.get('files',[])) if isinstance(result.get('files'),list) else None))
        if count is not None: summary=f"{count} Ergebnisse"
    return ToolCardView(kind,name,'completed',summary,tuple(details),100,changed,protected,call_id=call_id)

def compact_layout(width:int) -> bool:
    return layout_mode(width) is LayoutMode.COMPACT
