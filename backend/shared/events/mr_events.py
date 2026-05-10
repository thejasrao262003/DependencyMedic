from pydantic import BaseModel


class MrCreatedPayload(BaseModel):
    merge_request_id: str
    repository_id: str
    patch_attempt_id: str
    gitlab_mr_id: str
    title: str
    mr_url: str
    reviewers: list[str]


class MrUpdatedPayload(BaseModel):
    merge_request_id: str
    repository_id: str
    gitlab_mr_id: str
    status: str
    approved: bool
