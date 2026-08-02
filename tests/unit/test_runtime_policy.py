from dataclasses import dataclass
from pathlib import Path
import pytest
from comptext_phone_agent.runtime.policy import RuntimePolicy, ToolPolicy

@dataclass
class Spec:
    policy: ToolPolicy
    parameters: dict = None
    def __post_init__(self):
        if self.parameters is None: self.parameters={"type":"object","properties":{},"additionalProperties":False}

class Registry:
    def __init__(self):
        self.items={
            'scan':Spec(ToolPolicy('scan',read_only=True,storage_intensive=True),{'type':'object','properties':{'path':{'type':'string'}},'additionalProperties':False}),
            'plan':Spec(ToolPolicy('plan',risk=1,read_only=False,approval='never')),
            'apply':Spec(ToolPolicy('apply',risk=2,read_only=False,approval='always')),
        }
    def get(self,name): return self.items.get(name)


def test_unknown_tool_and_path_escape_rejected(tmp_path):
    p=RuntimePolicy(Registry(),tmp_path)
    with pytest.raises(ValueError,match='not allowed'): p.prepare(call_id='1',name='shell',arguments={})
    with pytest.raises(ValueError,match='outside'): p.prepare(call_id='1',name='scan',arguments={'path':'../secret'})


def test_safe_mode_only_allows_read_only(tmp_path):
    p=RuntimePolicy(Registry(),tmp_path,safe_mode=True)
    assert p.authorize(p.prepare(call_id='1',name='scan',arguments={})).allowed
    with pytest.raises(ValueError,match='safe mode'): p.prepare(call_id='2',name='plan',arguments={})


def test_approval_tool_interrupts(tmp_path):
    p=RuntimePolicy(Registry(),tmp_path)
    decision=p.authorize(p.prepare(call_id='1',name='apply',arguments={}))
    assert not decision.allowed and decision.requires_approval

def test_schema_rejects_unknown_wrong_type_and_range(tmp_path):
    class RichRegistry(Registry):
        def __init__(self):
            super().__init__()
            self.items['scan'].parameters={'type':'object','properties':{'top':{'type':'integer','minimum':1,'maximum':100}},'additionalProperties':False}
    p=RuntimePolicy(RichRegistry(),tmp_path)
    with pytest.raises(ValueError,match='unknown tool arguments'): p.prepare(call_id='1',name='scan',arguments={'shell':'x'})
    with pytest.raises(ValueError,match='invalid type'): p.prepare(call_id='1',name='scan',arguments={'top':'30'})
    with pytest.raises(ValueError,match='above maximum'): p.prepare(call_id='1',name='scan',arguments={'top':101})
