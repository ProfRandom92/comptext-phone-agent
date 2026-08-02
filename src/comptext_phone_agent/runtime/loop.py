from __future__ import annotations
from dataclasses import dataclass
import json
from typing import Any
from .limits import LoopBudget, LoopLimitError
from .model import RuntimeModel, ModelTurn
from .policy import RuntimePolicy
from .state import CancellationToken, RunState, RunStateMachine
from .store import RuntimeStore
from .signals import SignalType


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    run_id: str
    state: str
    answer: str
    stop_reason: str
    approval_id: str | None = None


class AgentRuntime:
    def __init__(self, *, store: RuntimeStore, model: RuntimeModel, registry, policy: RuntimePolicy,
                 budget_factory=LoopBudget, result_projector=None):
        self.store=store; self.model=model; self.registry=registry; self.policy=policy
        self.budget_factory=budget_factory; self.result_projector=result_projector or (lambda value: value)

    def run(self, goal: str, session_id: str, *, history: list[dict[str,Any]] | None=None,
            resume_run_id: str | None=None, cancellation: CancellationToken | None=None, event_callback=None) -> AgentRunResult:
        token=cancellation or CancellationToken(); budget=self.budget_factory()
        run=self.store.load_run(resume_run_id) if resume_run_id else self.store.create_run(session_id,goal)
        if run is None: raise ValueError(f"run not found: {resume_run_id}")
        def emit(event_type: str, payload: dict[str, Any] | None=None):
            event=self.store.append_event(run.id,event_type,payload or {})
            if event_callback is not None:
                event_callback(event)
            return event
        machine=RunStateMachine(RunState(run.state) if resume_run_id else RunState.IDLE)
        if not resume_run_id:
            machine.transition(RunState.PLANNING)
            emit('run.started.v1',{'goal':goal})
        messages=list(history or [])+[{'role':'user','content':goal}]
        answer=''; approval_id=None
        try:
            while True:
                if self.store.consume_signal(run.id,SignalType.CANCEL): token.cancel()
                if token.cancelled:
                    if machine.state not in {RunState.CANCELLED,RunState.COMPLETED,RunState.FAILED}: machine.transition(RunState.CANCELLED)
                    emit('run.cancelled.v1',{})
                    self.store.update_run(run.id,state='cancelled',stop_reason='cancelled')
                    return AgentRunResult(run.id,'cancelled',answer,'cancelled')
                if machine.state in {RunState.PLANNING,RunState.OBSERVING}:
                    machine.transition(RunState.WAITING_MODEL)
                budget.record_model_turn()
                emit('model.started.v1',{'turn':budget.model_turns})
                turn=self.model.complete(messages,self.registry.schemas(self.policy.safe_mode))
                emit('model.completed.v1',{'content':turn.content,'tool_calls':len(turn.tool_calls)})
                if not turn.tool_calls:
                    answer=turn.content.strip() or 'Keine lesbare Antwort erhalten.'
                    machine.transition(RunState.COMPLETED)
                    emit('run.completed.v1',{'answer':answer})
                    self.store.update_run(run.id,state='completed',stop_reason='final_answer')
                    return AgentRunResult(run.id,'completed',answer,'final_answer')
                machine.transition(RunState.VALIDATING_TOOL)
                assistant_calls=[]
                for proposal in turn.tool_calls:
                    budget.record_tool_call(proposal.name,proposal.arguments)
                    emit('tool.proposed.v1',{'call_id':proposal.call_id,'name':proposal.name,'arguments':proposal.arguments})
                    prepared=self.policy.prepare(call_id=proposal.call_id,name=proposal.name,arguments=proposal.arguments)
                    decision=self.policy.authorize(prepared)
                    emit('tool.validated.v1',{'call_id':proposal.call_id,'name':proposal.name,'allowed':decision.allowed,'reason':decision.reason})
                    if decision.requires_approval:
                        machine.transition(RunState.WAITING_APPROVAL)
                        approval_id=f"runtime:{run.id}:{proposal.call_id}"
                        emit('approval.requested.v1',{'approval_id':approval_id,'tool':proposal.name,'arguments':prepared.arguments})
                        self.store.update_run(run.id,state='waiting_approval',stop_reason='approval_required')
                        return AgentRunResult(run.id,'waiting_approval',turn.content,'approval_required',approval_id)
                    if not decision.allowed:
                        raise PermissionError(decision.reason)
                    if machine.state is RunState.VALIDATING_TOOL: machine.transition(RunState.RUNNING_TOOL)
                    key=self.store.tool_idempotency_key(run.id,proposal.call_id,proposal.name,prepared.arguments)
                    cached=self.store.load_tool_result(key)
                    emit('tool.started.v1',{'call_id':proposal.call_id,'name':proposal.name,'idempotency_key':key,'replayed':cached is not None})
                    try:
                        result=cached if cached is not None else self.registry.execute(proposal.name,prepared.arguments)
                        if cached is None: self.store.save_tool_result(key,run.id,proposal.call_id,proposal.name,result)
                    except Exception as exc:
                        emit('tool.failed.v1',{'call_id':proposal.call_id,'name':proposal.name,'error':type(exc).__name__})
                        raise
                    emit('tool.completed.v1',{'call_id':proposal.call_id,'name':proposal.name,'result':result})
                    assistant_calls.append({'function':{'name':proposal.name,'arguments':proposal.arguments}})
                    projected=self.result_projector(result)
                    messages.append({'role':'tool','tool_name':proposal.name,'content':json.dumps(projected,ensure_ascii=False)})
                    if isinstance(result,dict) and result.get('approval_required'):
                        machine.transition(RunState.WAITING_APPROVAL)
                        approval_id=str(result.get('plan',{}).get('id') or f"runtime:{run.id}:{proposal.call_id}")
                        emit('approval.requested.v1',{'approval_id':approval_id,'tool':proposal.name,'plan_only':True})
                        self.store.update_run(run.id,state='waiting_approval',stop_reason='plan_ready')
                        return AgentRunResult(run.id,'waiting_approval',turn.content,'plan_ready',approval_id)
                messages.insert(max(0,len(messages)-len(assistant_calls)),{'role':'assistant','content':turn.content,'tool_calls':assistant_calls})
                machine.transition(RunState.OBSERVING)
        except LoopLimitError as exc:
            emit('run.failed.v1',{'reason':exc.reason})
            self.store.update_run(run.id,state='failed',stop_reason=exc.reason,error=exc.reason)
            return AgentRunResult(run.id,'failed',answer,exc.reason)
        except Exception as exc:
            if machine.state not in {RunState.FAILED,RunState.COMPLETED,RunState.CANCELLED}: machine.transition(RunState.FAILED)
            emit('run.failed.v1',{'error':type(exc).__name__})
            self.store.update_run(run.id,state='failed',stop_reason='error',error=str(exc))
            return AgentRunResult(run.id,'failed',answer,'error')
