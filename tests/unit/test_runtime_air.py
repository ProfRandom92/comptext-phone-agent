from comptext_phone_agent.runtime.air import runtime_event_to_air
from comptext_phone_agent.runtime.events import RuntimeEvent

def test_runtime_events_map_to_air_without_hidden_reasoning():
    event=RuntimeEvent.create(run_id='r',sequence=1,event_type='approval.requested.v1',payload={'tool':'cleanup'})
    air=runtime_event_to_air(event)
    assert air['type']=='approval_requested' and air['event_hash']==event.event_hash
    assert 'thought' not in air and 'chain_of_thought' not in air
