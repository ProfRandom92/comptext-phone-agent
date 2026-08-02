from comptext_phone_agent.runtime.events import RuntimeEvent
from comptext_phone_agent.tui.card_factory import card_from_event
from comptext_phone_agent.tui.reducer import reduce_events

def ev(seq,kind,payload):
    return RuntimeEvent.create(run_id='r',sequence=seq,event_type=kind,payload=payload,timestamp=f'2026-08-01T12:00:{seq:02d}+00:00')

def test_card_catalog_and_unknown_fallback():
    storage=card_from_event(ev(1,'tool.completed.v1',{'name':'scan_storage','result':{'total_files':12,'total_size':1024}}))
    dup=card_from_event(ev(2,'tool.completed.v1',{'name':'find_duplicates','result':{'group_count':3}}))
    unknown=card_from_event(ev(3,'custom.widget.v1',{'widget':'evil'}))
    assert storage.kind=='storage' and storage.progress==100
    assert dup.kind=='duplicates' and unknown.kind=='generic'

def test_event_reducer_builds_safe_transcript():
    state=reduce_events([ev(1,'run.started.v1',{'goal':'x'}),ev(2,'tool.started.v1',{'name':'scan_storage'}),ev(3,'tool.completed.v1',{'name':'scan_storage','result':{'total_files':5}}),ev(4,'run.completed.v1',{'answer':'fertig'})])
    assert state.stop_reason=='final_answer'
    assert any(i.tool and i.tool.kind=='storage' for i in state.items)
    assert state.items[-1].body=='fertig'
