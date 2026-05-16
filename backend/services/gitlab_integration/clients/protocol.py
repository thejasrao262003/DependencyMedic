"""GitLab client protocol — separates business logic from transport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class CommitFile:
    path: str
    content: str
    action: str = "update"


@dataclass
class CommitResult:
    branch: str
    sha: str


@dataclass
class PipelineSnapshot:
    pipeline_id: str
    status: str  # "pending" | "running" | "success" | "failed" | "canceled"
    failed_stage: str | None
    logs_url: str
    raw_logs: str | None


@dataclass
class MergeRequestResult:
    iid: str
    web_url: str


@runtime_checkable
class GitLabClient(Protocol):
    async def create_branch(
        self, project_id: str, branch: str, ref: str
    ) -> None: ...

    async def commit_files(
        self,
        project_id: str,
        branch: str,
        message: str,
        files: list[CommitFile],
    ) -> CommitResult: ...

    async def trigger_pipeline(
        self, project_id: str, ref: str
    ) -> PipelineSnapshot: ...

    async def get_pipeline(
        self, project_id: str, pipeline_id: str
    ) -> PipelineSnapshot: ...

    async def create_merge_request(
        self,
        project_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        reviewers: list[str],
    ) -> MergeRequestResult: ...

    async def aclose(self) -> None: ...
