from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.runtime.store import RuntimeStore


def test_runtime_store_chains_and_resumes(tmp_path):
    store=RuntimeStore(Database(tmp_path/'state.sqlite3'))
    run=store.create_run('session','goal')
    first=store.append_event(run.id,'run.started.v1',{'goal':'goal'})
    second=store.append_event(run.id,'model.started.v1',{})
    events=store.list_events(run.id)
    assert [x.sequence for x in events] == [1,2]
    assert second.parent_event_hash == first.event_hash
    assert all(x.verify() for x in events)
    assert store.load_run(run.id).goal == 'goal'
