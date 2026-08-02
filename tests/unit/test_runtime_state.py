import pytest
from comptext_phone_agent.runtime.state import RunState, RunStateMachine, InvalidStateTransition, CancellationToken


def test_state_machine_accepts_documented_path():
    m=RunStateMachine();
    for state in [RunState.PLANNING,RunState.WAITING_MODEL,RunState.VALIDATING_TOOL,RunState.RUNNING_TOOL,RunState.OBSERVING,RunState.COMPLETED]:
        m.transition(state)
    assert m.state is RunState.COMPLETED


def test_state_machine_rejects_shortcut():
    with pytest.raises(InvalidStateTransition): RunStateMachine().transition(RunState.RUNNING_TOOL)


def test_cancellation_token():
    token=CancellationToken(); assert not token.cancelled; token.cancel(); assert token.cancelled
