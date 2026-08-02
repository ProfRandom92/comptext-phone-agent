from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.runtime.signals import SignalType
from comptext_phone_agent.runtime.store import RuntimeStore
from tests.unit.test_runtime_loop import FakeModel, ModelTurn, ToolProposal, runtime

def test_durable_signal_roundtrip(tmp_path):
    store=RuntimeStore(Database(tmp_path/'state.sqlite3')); run=store.create_run('s','g')
    store.append_signal(run.id,SignalType.CANCEL,{'reason':'user'})
    assert store.list_signals(run.id,unconsumed_only=True)[0].payload['reason']=='user'
    assert store.consume_signal(run.id,SignalType.CANCEL).consumed_at
    assert not store.list_signals(run.id,unconsumed_only=True)

def test_tool_result_is_idempotent_for_same_run_call(tmp_path):
    model=FakeModel(ModelTurn('',[ToolProposal('same','scan',{})]),ModelTurn('ok'))
    rt,store,reg=runtime(tmp_path,model)
    out=rt.run('x','s')
    assert out.state=='completed' and len(reg.calls)==1
    key=store.tool_idempotency_key(out.run_id,'same','scan',{})
    assert store.load_tool_result(key)=={'ok':True,'changed':False}

def test_cancel_signal_stops_before_model(tmp_path):
    rt,store,_=runtime(tmp_path,FakeModel(ModelTurn('never')))
    run=store.create_run('s','x')
    store.append_signal(run.id,SignalType.CANCEL)
    out=rt.run('x','s',resume_run_id=run.id)
    assert out.state=='cancelled'
