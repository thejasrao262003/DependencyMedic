from pydantic import BaseModel


class DependencyChange(BaseModel):
    package: str
    from_version: str
    to_version: str


class PatchGeneratedPayload(BaseModel):
    patch_attempt_id: str
    repository_id: str
    vulnerability_id: str
    branch_name: str
    dependency_changes: list[DependencyChange]
    attempt_number: int


class PatchRetryRequestedPayload(BaseModel):
    patch_attempt_id: str
    repository_id: str
    vulnerability_id: str
    pipeline_run_id: str
    failure_type: str
    retry_reason: str
    attempt_number: int


class PatchValidatedPayload(BaseModel):
    patch_attempt_id: str
    repository_id: str
    vulnerability_id: str
    branch_name: str
    pipeline_run_id: str
