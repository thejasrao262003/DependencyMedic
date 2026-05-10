from datetime import datetime
from pydantic import BaseModel
from ..enums import RepoStatus


class RepositorySchema(BaseModel):
    id: str
    repo_name: str
    gitlab_project_id: str
    default_branch: str = "main"
    languages: list[str] = []
    repo_url: str
    ci_enabled: bool = True
    last_scanned_commit: str | None = None
    status: RepoStatus = RepoStatus.ACTIVE
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime
