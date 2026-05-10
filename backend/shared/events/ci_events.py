from pydantic import BaseModel


class CiStartedPayload(BaseModel):
    pipeline_run_id: str
    patch_attempt_id: str
    repository_id: str
    gitlab_pipeline_id: str
    branch_name: str


class CiFailedPayload(BaseModel):
    pipeline_run_id: str
    patch_attempt_id: str
    repository_id: str
    gitlab_pipeline_id: str
    failed_stage: str
    failure_summary: str
    logs_url: str
    attempt_number: int
