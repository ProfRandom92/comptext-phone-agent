from __future__ import annotations
import secrets
from .models import OrchestratorResult, RouteDecision, RouteKind
from .router import RouterError

class OrchestratorService:
    def __init__(self,*,router,registry,catalog,policy,min_confidence:float=0.8):
        self.router=router; self.registry=registry; self.catalog=catalog; self.policy=policy
        self.min_confidence=min_confidence
    def handle(self,text:str,*,execute:bool=False) -> OrchestratorResult:
        try:
            decision=self.router.route(text)
        except RouterError as exc:
            return OrchestratorResult(
                decision=RouteDecision(RouteKind.REJECT,reason='router_error',source='router'),
                status='error',error=exc.category,
            )
        except Exception:
            return OrchestratorResult(
                decision=RouteDecision(RouteKind.REJECT,reason='router_failure',source='router'),
                status='error',error='router_error',
            )
        if decision.kind is not RouteKind.DIRECT_ACTION:
            return OrchestratorResult(decision,decision.kind.value)
        if decision.confidence < self.min_confidence:
            return OrchestratorResult(decision,'delegate')
        if not decision.action or self.catalog.get(decision.action) is None:
            return OrchestratorResult(decision,'rejected',error='action_not_allowed')
        try:
            prepared=self.policy.prepare(call_id=secrets.token_hex(8),name=decision.action,arguments=decision.arguments)
            authorization=self.policy.authorize(prepared)
        except (TypeError,ValueError):
            return OrchestratorResult(decision,'rejected',error='invalid_arguments')
        if authorization.requires_approval:
            return OrchestratorResult(decision,'approval_required',approval_required=True,error=authorization.reason)
        if not authorization.allowed:
            return OrchestratorResult(decision,'rejected',error=authorization.reason)
        if not execute:
            return OrchestratorResult(decision,'preview',result={'action':prepared.name,'arguments':prepared.arguments})
        try:
            result=self.registry.execute(prepared.name,prepared.arguments)
        except Exception:
            return OrchestratorResult(decision,'rejected',error='action_failed')
        approval=bool(isinstance(result,dict) and result.get('approval_required'))
        return OrchestratorResult(decision,'approval_required' if approval else 'completed',result=result,approval_required=approval)
