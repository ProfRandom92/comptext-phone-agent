from pydantic import BaseModel
class ApprovalRequest(BaseModel):
    plan_id: str
    phrase: str
class ScanRequest(BaseModel):
    path: str
