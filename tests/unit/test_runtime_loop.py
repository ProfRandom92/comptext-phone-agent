from dataclasses import dataclass
from pathlib import Path
from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.runtime.loop import AgentRuntime
from comptext_phone_agent.runtime.model import ModelTurn, ToolProposal
from comptext_phone_agent.runtime.policy import RuntimePolicy, ToolPolicy
from comptext_phone_agent.runtime.store import RuntimeStore
from comptext_phone_agent.runtime.state import CancellationToken
from comptext_phone_agent.runtime.limits import LoopBudget

@dataclass
class Spec:
    policy: ToolPolicy
    parameters: dict = None
    def __post_init__(self):
        if self.parameters is None: self.parameters={"type":"object","properties":{},"additionalProperties":False}
    def ollama_schema(self): return {'type':'function','function':{'name':self.policy.name,'parameters':{'type':'object'}}}
class Registry:
    def __init__(self):
        self.items={'scan':Spec(ToolPolicy('scan',read_only=True)),'apply':Spec(ToolPolicy('apply',read_only=False,approval='always'))}
        self.calls=[]
    def get(self,n): return self.items.get(n)
    def schemas(self,safe_mode=False): return [x.ollama_schema() for x in self.items.values() if not safe_mode or x.policy.read_only]
    def execute(self,n,a): self.calls.append((n,a)); return {'ok':True,'changed':False}
class FakeModel:
    def __init__(self,*turns): self.turns=list(turns)
    def complete(self,messages,tools): return self.turns.pop(0)

def runtime(tmp_path,model,registry=None,budget_factory=LoopBudget,safe=False):
    reg=registry or Registry(); store=RuntimeStore(Database(tmp_path/'state.sqlite3'))
    return AgentRuntime(store=store,model=model,registry=reg,policy=RuntimePolicy(reg,tmp_path,safe),budget_factory=budget_factory),store,reg

def test_final_answer(tmp_path):
    r,s,_=runtime(tmp_path,FakeModel(ModelTurn('fertig')))
    out=r.run('ziel','session'); assert out.state=='completed' and out.answer=='fertig'
    assert s.list_events(out.run_id)[-1].event_type=='run.completed.v1'

def test_multi_step_tool_loop(tmp_path):
    r,s,reg=runtime(tmp_path,FakeModel(ModelTurn('',[ToolProposal('1','scan',{})]),ModelTurn('Analyse fertig')))
    out=r.run('analysiere','session'); assert out.state=='completed'; assert reg.calls==[('scan',{})]
    assert any(e.event_type=='tool.completed.v1' for e in s.list_events(out.run_id))

def test_approval_interrupt(tmp_path):
    r,s,_=runtime(tmp_path,FakeModel(ModelTurn('',[ToolProposal('1','apply',{})])))
    out=r.run('apply','session'); assert out.state=='waiting_approval' and out.approval_id
    assert s.load_run(out.run_id).state=='waiting_approval'

def test_repeat_guard_stops(tmp_path):
    turns=[ModelTurn('',[ToolProposal(str(i),'scan',{})]) for i in range(3)]
    r,_,_=runtime(tmp_path,FakeModel(*turns),budget_factory=lambda:LoopBudget(max_identical_calls=2))
    out=r.run('loop','session'); assert out.stop_reason=='repeated_tool_call'

def test_cancelled_before_model(tmp_path):
    r,_,_=runtime(tmp_path,FakeModel(ModelTurn('never'))); token=CancellationToken(); token.cancel()
    assert r.run('x','s',cancellation=token).state=='cancelled'

def test_result_projector_controls_model_observation(tmp_path):
    class ObservingModel:
        def __init__(self): self.turn=0; self.seen=None
        def complete(self,messages,tools):
            self.turn+=1
            if self.turn==1: return ModelTurn('',[ToolProposal('1','scan',{})])
            self.seen=messages[-1]['content']; return ModelTurn('ok')
    model=ObservingModel(); reg=Registry(); store=RuntimeStore(Database(tmp_path/'state.sqlite3'))
    rt=AgentRuntime(store=store,model=model,registry=reg,policy=RuntimePolicy(reg,tmp_path),result_projector=lambda _: {'redacted':True})
    assert rt.run('x','s').state=='completed'
    assert model.seen=='{"redacted": true}'
