"""Real GitLab REST v4 client.

We deliberately keep the surface tiny — only the calls used by the remediation
flow. Anything outside that surface goes through the mock client.
"""

from __future__ import annotations

import base64
from urllib.parse import quote

import httpx

from .protocol import (
    CommitFile,
    CommitResult,
    MergeRequestResult,
    PipelineSnapshot,
)


class GitLabAPIError(RuntimeError):
    pass


_STATUS_MAP = {
    "created": "pending",
    "waiting_for_resource": "pending",
    "preparing": "pending",
    "pending": "pending",
    "running": "running",
    "success": "success",
    "failed": "failed",
    "canceled": "canceled",
    "skipped": "canceled",
    "manual": "pending",
    "scheduled": "pending",
}


class GitLabHttpClient:
    def __init__(self, base_url: str, token: str, *, timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/") + "/api/v4"
        self._client = httpx.AsyncClient(
            headers={"PRIVATE-TOKEN": token},
            timeout=timeout,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def create_branch(
        self, project_id: str, branch: str, ref: str
    ) -> None:
        url = f"{self._base}/projects/{quote(project_id, safe='')}/repository/branches"
        resp = await self._client.post(url, params={"branch": branch, "ref": ref})
        if resp.status_code in (201, 200):
            return
        if resp.status_code == 400 and "already exists" in resp.text.lower():
            return
        raise GitLabAPIError(f"create_branch {resp.status_code}: {resp.text}")

    async def commit_files(
        self,
        project_id: str,
        branch: str,
        message: str,
        files: list[CommitFile],
    ) -> CommitResult:
        url = f"{self._base}/projects/{quote(project_id, safe='')}/repository/commits"
        actions = [
            {
                "action": f.action,
                "file_path": f.path,
                "content": base64.b64encode(f.content.encode()).decode(),
                "encoding": "base64",
            }
            for f in files
        ]
        resp = await self._client.post(
            url,
            json={"branch": branch, "commit_message": message, "actions": actions},
        )
        if resp.status_code not in (200, 201):
            raise GitLabAPIError(f"commit_files {resp.status_code}: {resp.text}")
        body = resp.json()
        return CommitResult(branch=branch, sha=body.get("id", ""))

    async def trigger_pipeline(
        self, project_id: str, ref: str
    ) -> PipelineSnapshot:
        url = f"{self._base}/projects/{quote(project_id, safe='')}/pipeline"
        resp = await self._client.post(url, params={"ref": ref})
        if resp.status_code not in (200, 201):
            raise GitLabAPIError(f"trigger_pipeline {resp.status_code}: {resp.text}")
        body = resp.json()
        return PipelineSnapshot(
            pipeline_id=str(body["id"]),
            status=_STATUS_MAP.get(body.get("status", "pending"), "pending"),
            failed_stage=None,
            logs_url=body.get("web_url", ""),
            raw_logs=None,
        )

    async def get_pipeline(
        self, project_id: str, pipeline_id: str
    ) -> PipelineSnapshot:
        proj = quote(project_id, safe="")
        resp = await self._client.get(f"{self._base}/projects/{proj}/pipelines/{pipeline_id}")
        if resp.status_code != 200:
            raise GitLabAPIError(f"get_pipeline {resp.status_code}: {resp.text}")
        body = resp.json()
        status = _STATUS_MAP.get(body.get("status", "pending"), "pending")
        failed_stage = None
        raw_logs = None

        if status == "failed":
            jobs_resp = await self._client.get(
                f"{self._base}/projects/{proj}/pipelines/{pipeline_id}/jobs"
            )
            if jobs_resp.status_code == 200:
                jobs = jobs_resp.json()
                failed_jobs = [j for j in jobs if j.get("status") == "failed"]
                if failed_jobs:
                    failed_stage = failed_jobs[0].get("stage")
                    job_id = failed_jobs[0].get("id")
                    if job_id:
                        trace = await self._client.get(
                            f"{self._base}/projects/{proj}/jobs/{job_id}/trace"
                        )
                        if trace.status_code == 200:
                            raw_logs = trace.text[-8000:]
        return PipelineSnapshot(
            pipeline_id=str(body["id"]),
            status=status,
            failed_stage=failed_stage,
            logs_url=body.get("web_url", ""),
            raw_logs=raw_logs,
        )

    async def create_merge_request(
        self,
        project_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        reviewers: list[str],
    ) -> MergeRequestResult:
        url = f"{self._base}/projects/{quote(project_id, safe='')}/merge_requests"
        resp = await self._client.post(
            url,
            json={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
                "reviewer_ids": [],
            },
        )
        if resp.status_code not in (200, 201):
            raise GitLabAPIError(f"create_mr {resp.status_code}: {resp.text}")
        body = resp.json()
        return MergeRequestResult(iid=str(body["iid"]), web_url=body.get("web_url", ""))
