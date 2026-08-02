from __future__ import annotations
import secrets
from .models import OrchestratorResult, RouteKind

class OrchestratorService:
    def __init__(self,*,router,registry,catalog,policy,min_confidence:float=0.8):
        self.router=router; self.registry=registry; self.catalog=catalog; self.policy=policy
        self.min_confidence=min_confidence
    def handle(self,text:str,*,execute:bool=False) -> OrchestratorResult:
        try:
            decision=self.router.route(text)
        except Exception as exc:
            return OrchestratorResult(
                decision=__import__('comptext_phone_agent.orchestrator.models',fromlist=['RouteDecision']).RouteDecision(RouteKind.PLANNER,reason='router_unavailable',source='fallback'),
                status='planner',error=type(exc).__name__,
            )
        if decision.kind is not RouteKind.DIRECT_ACTION:
            return OrchestratorResult(decision,'planner' if decision.kind is RouteKind.PLANNER else decision.kind.value)
        if decision.confidence < self.min_confidence:
            return OrchestratorResult(decision,'planner')
        if not decision.action or self.catalog.get(decision.action) is None:
            return OrchestratorResult(decision,'rejected',error='action_not_allowed')
        try:
            prepared=self.policy.prepare(call_id=secrets.token_hex(8),name=decision.action,arguments=decision.arguments)
            authorization=self.policy.authorize(prepared)
        except Exception as exc:
            return OrchestratorResult(decision,'rejected',error=str(exc))
        if authorization.requires_approval:
            return OrchestratorResult(decision,'approval_required',approval_required=True,error=authorization.reason)
        if not authorization.allowed:
            return OrchestratorResult(decision,'rejected',error=authorization.reason)
        if not execute:
            return OrchestratorResult(decision,'preview',result={'action':prepared.name,'arguments':prepared.arguments})
        result=self.registry.execute(prepared.name,prepared.arguments)
        approval=bool(isinstance(result,dict) and result.get('approval_required'))
        return OrchestratorResult(decision,'approval_required' if approval else 'completed',result=result,approval_required=approval)
