from __future__ import annotations
from pathlib import Path
import json, os, secrets, time, uuid
from ..audit.database import Database
from ..audit.logger import AuditLogger
from ..models import ActionPlan, ApprovalClaims, OperatingMode, PlanAction, RiskClass
from .policy import PolicyError, confirmation_phrase
from .tokens import decode, encode, token_hash

class ApprovalEngine:
    def __init__(self, database: Database, data_dir: Path, installation_id: str = "local", user_id: str = "local"):
        self.database = database
        self.data_dir = data_dir
        self.installation_id = installation_id
        self.user_id = user_id
        self.audit = AuditLogger(database)
        self.secret = self._load_secret()
    def _load_secret(self) -> bytes:
        path = self.data_dir / "approval.key"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(secrets.token_bytes(32))
            os.chmod(path, 0o600)
        return path.read_bytes()
    def save_plan(self, plan: ActionPlan) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO plans(id,body,plan_hash,created_at) VALUES(?,?,?,?)",
                (plan.id, json.dumps(plan.to_dict()), plan.plan_hash, plan.created_at),
            )
    def load_plan(self, plan_id: str) -> ActionPlan:
        with self.database.connect() as connection:
            row = connection.execute("SELECT body FROM plans WHERE id=?", (plan_id,)).fetchone()
        if not row:
            raise KeyError(f"plan not found: {plan_id}")
        data = json.loads(row[0])
        actions = [PlanAction(x["action"], x["source"], x.get("target"), x["size"], x["reason"], RiskClass(x["risk"])) for x in data["actions"]]
        return ActionPlan(data["id"], data["session_id"], data["created_at"], OperatingMode(data["mode"]), actions, data["description"])
    def approve(self, plan: ActionPlan, phrase: str, ttl_seconds: int = 900) -> tuple[str, ApprovalClaims]:
        expected = confirmation_phrase(plan.risk)
        if phrase != expected:
            raise PolicyError(f"confirmation phrase must be exactly: {expected}")
        now = int(time.time())
        claims = ApprovalClaims(
            str(uuid.uuid4()), self.installation_id, self.user_id, plan.session_id,
            ",".join(sorted({action.action for action in plan.actions})),
            [action.source for action in plan.actions],
            [action.target for action in plan.actions if action.target],
            len(plan.actions), plan.total_size, plan.plan_hash, now, now + ttl_seconds,
            int(plan.risk), secrets.token_hex(12),
        )
        token = encode(claims.to_dict(), self.secret)
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO approvals(id,plan_hash,token_hash,created_at,expires_at,risk) VALUES(?,?,?,?,?,?)",
                (claims.approval_id, claims.plan_hash, token_hash(token), claims.created_at, claims.expires_at, claims.risk),
            )
        self.audit.log(action="approval.created", tool="approval", parameters={"risk": claims.risk, "expires_at": claims.expires_at}, paths=claims.sources, plan_id=plan.id, approval_id=claims.approval_id)
        return token, claims
    def verify(self, token: str, plan: ActionPlan, consume: bool = True) -> ApprovalClaims:
        claims = ApprovalClaims(**decode(token, self.secret))
        now = int(time.time())
        if claims.installation_id != self.installation_id or claims.user_id != self.user_id:
            raise PolicyError("approval bound to another installation/user")
        if claims.session_id != plan.session_id:
            raise PolicyError("approval bound to another session")
        if claims.plan_hash != plan.plan_hash:
            raise PolicyError("plan changed after approval")
        if claims.expires_at < now:
            raise PolicyError("approval expired")
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM approvals WHERE id=?", (claims.approval_id,)).fetchone()
            if not row or row["revoked"]:
                raise PolicyError("approval unavailable or revoked")
            if row["token_hash"] != token_hash(token):
                raise PolicyError("approval token mismatch")
            if row["consumed_at"] is not None:
                raise PolicyError("approval already used")
            if consume:
                connection.execute("UPDATE approvals SET consumed_at=? WHERE id=?", (now, claims.approval_id))
        if consume:
            self.audit.log(action="approval.consumed", tool="approval", paths=claims.sources, plan_id=plan.id, approval_id=claims.approval_id)
        return claims
