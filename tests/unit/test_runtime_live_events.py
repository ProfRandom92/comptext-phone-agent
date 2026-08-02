from tests.unit.test_runtime_loop import FakeModel, ModelTurn, ToolProposal, runtime

def test_runtime_emits_persisted_events_in_order(tmp_path):
    rt,store,_=runtime(tmp_path,FakeModel(ModelTurn('',[ToolProposal('1','scan',{})]),ModelTurn('done')))
    seen=[]
    def callback(event):
        persisted=store.list_events(event.run_id)
        assert persisted[-1].event_hash==event.event_hash
        seen.append((event.sequence,event.event_type))
    out=rt.run('scan','session',event_callback=callback)
    assert out.state=='completed'
    assert [seq for seq,_ in seen]==list(range(1,len(seen)+1))
    assert 'tool.started.v1' in [kind for _,kind in seen]
    assert seen[-1][1]=='run.completed.v1'
