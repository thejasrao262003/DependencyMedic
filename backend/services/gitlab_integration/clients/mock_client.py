"""In-process GitLab simulator for demos and CI.

Behaviour is deterministic and scripted so the demo can show a realistic
fail-then-pass cycle without network access.

Scripting rules:
- Any branch ending in `-attempt-1` fails the first pipeline run with a
  scripted dependency-conflict log.
- Any branch ending in `-attempt-2` (or higher) passes.
- Branches that don't follow the scheme always pass (covers ad-hoc test runs).
"""

from __future__ import annotations

import asyncio
import re
import uuid
from typing import Any

from .protocol import (
    CommitFile,
    CommitResult,
    MergeRequestResult,
    PipelineSnapshot,
)

_FAIL_LOG = """\
Running unit tests
ImportError: cannot import name 'foo' from 'somepkg'
TypeError: validate() takes 2 positional arguments but 3 were given
  File "tests/test_payment.py", line 42, in test_validate_amount
ERROR: tests/test_payment.py::test_validate_amount - TypeError
1 failed, 12 passed in 4.21s
"""

_ATTEMPT_RE = re.compile(r"-attempt-(\d+)$")


def _attempt_number(branch: str) -> int:
    m = _ATTEMPT_RE.search(branch)
    return int(m.group(1)) if m else 99


class MockGitLabClient:
    def __init__(self) -> None:
        self._pipelines: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create_branch(self, project_id: str, branch: str, ref: str) -> None:
        await asyncio.sleep(0)

    async def commit_files(
        self,
        project_id: str,
        branch: str,
        message: str,
        files: list[CommitFile],
    ) -> CommitResult:
        await asyncio.sleep(0)
        return CommitResult(branch=branch, sha=uuid.uuid4().hex[:12])

    async def trigger_pipeline(
        self, project_id: str, ref: str
    ) -> PipelineSnapshot:
        async with self._lock:
            pipeline_id = str(uuid.uuid4())
            attempt = _attempt_number(ref)
            self._pipelines[pipeline_id] = {
                "ref": ref,
                "attempt": attempt,
                "ticks": 0,
            }
        return PipelineSnapshot(
            pipeline_id=pipeline_id,
            status="running",
            failed_stage=None,
            logs_url=f"https://mock-gitlab/{project_id}/pipelines/{pipeline_id}",
            raw_logs=None,
        )

    async def get_pipeline(
        self, project_id: str, pipeline_id: str
    ) -> PipelineSnapshot:
        async with self._lock:
            entry = self._pipelines.get(pipeline_id)
            if not entry:
                return PipelineSnapshot(
                    pipeline_id=pipeline_id,
                    status="failed",
                    failed_stage="unknown",
                    logs_url=f"https://mock-gitlab/{project_id}/pipelines/{pipeline_id}",
                    raw_logs="pipeline not found",
                )
            entry["ticks"] += 1
            attempt = entry["attempt"]
            ticks = entry["ticks"]

        # Resolve after a couple of polls so the dashboard sees a "running" state.
        if ticks < 2:
            return PipelineSnapshot(
                pipeline_id=pipeline_id,
                status="running",
                failed_stage=None,
                logs_url=f"https://mock-gitlab/{project_id}/pipelines/{pipeline_id}",
                raw_logs=None,
            )

        if attempt <= 1:
            return PipelineSnapshot(
                pipeline_id=pipeline_id,
                status="failed",
                failed_stage="unit_tests",
                logs_url=f"https://mock-gitlab/{project_id}/pipelines/{pipeline_id}",
                raw_logs=_FAIL_LOG,
            )
        return PipelineSnapshot(
            pipeline_id=pipeline_id,
            status="success",
            failed_stage=None,
            logs_url=f"https://mock-gitlab/{project_id}/pipelines/{pipeline_id}",
            raw_logs="all tests passed",
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
        iid = str(uuid.uuid4())[:8]
        return MergeRequestResult(
            iid=iid,
            web_url=f"https://mock-gitlab/{project_id}/-/merge_requests/{iid}",
        )

    async def aclose(self) -> None:
        return None
