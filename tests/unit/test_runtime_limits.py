import pytest
from comptext_phone_agent.runtime.limits import LoopBudget, LoopLimitError


def test_repeated_call_guard():
    budget=LoopBudget(max_identical_calls=2)
    budget.record_tool_call('scan',{'x':1}); budget.record_tool_call('scan',{'x':1})
    with pytest.raises(LoopLimitError, match='repeated_tool_call'): budget.record_tool_call('scan',{'x':1})


def test_turn_and_tool_limits():
    b=LoopBudget(max_model_turns=1); b.record_model_turn()
    with pytest.raises(LoopLimitError, match='model_turn_limit'): b.record_model_turn()
    b=LoopBudget(max_tool_calls=1); b.record_tool_call('a',{})
    with pytest.raises(LoopLimitError, match='tool_call_limit'): b.record_tool_call('b',{})
