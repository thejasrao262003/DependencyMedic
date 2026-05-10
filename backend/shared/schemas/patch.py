from datetime import datetime
from pydantic import BaseModel
from ..enums import PatchStatus


class DependencyChangeSchema(BaseModel):
    package: str
    from_version: str
    to_version: str


class PatchAttemptSchema(BaseModel):
    id: str
    repository_id: str
    vulnerability_id: str
    branch_name: str
    dependency_changes: list[DependencyChangeSchema] = []
    attempt_number: int = 1
    status: PatchStatus = PatchStatus.PENDING
    llm_used: bool = False
    confidence_score: float | None = None
    retry_reason: str | None = None
    patch_summary: str = ""
    created_at: datetime
    updated_at: datetime
