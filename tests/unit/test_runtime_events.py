from comptext_phone_agent.runtime.events import RuntimeEvent


def test_runtime_event_hash_is_deterministic():
    kwargs=dict(run_id="r",sequence=1,event_type="run.started.v1",payload={"b":2,"a":1},parent_event_hash=None,event_id="e",timestamp="2026-08-01T00:00:00+00:00")
    one=RuntimeEvent.create(**kwargs); two=RuntimeEvent.create(**kwargs)
    assert one.event_hash == two.event_hash
    assert one.verify()


def test_unknown_event_type_is_valid_and_preserved():
    event=RuntimeEvent.create(run_id="r",sequence=1,event_type="future.event.v9",payload={})
    assert event.event_type == "future.event.v9"
    assert event.verify()
