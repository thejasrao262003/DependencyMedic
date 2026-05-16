"""End-to-end pipeline orchestration for a generated patch."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from shared.constants import (
    COLLECTION_PATCH_ATTEMPTS,
    COLLECTION_PIPELINE_RUNS,
    COLLECTION_REPOSITORIES,
)
from shared.enums import PatchStatus, PipelineStatus
from shared.events.base import BaseEvent
from shared.events.ci_events import CiFailedPayload, CiStartedPayload
from shared.events.patch_events import PatchValidatedPayload
from shared.logging import get_logger
from shared.utils.mongo import get_database
from shared.utils.redis_streams import RedisStreamPublisher

from ..clients.protocol import CommitFile, GitLabClient

logger = get_logger("gitlab_integration.pipeline_runner")


async def run_patch_pipeline(
    *,
    client: GitLabClient,
    publisher: RedisStreamPublisher,
    patch_attempt_id: str,
    correlation_id: str,
    poll_interval: float,
    poll_timeout: float,
) -> None:
    db = get_database()
    patch = await db[COLLECTION_PATCH_ATTEMPTS].find_one({"_id": patch_attempt_id})
    if not patch:
        logger.warning(
            "pipeline_runner: patch_attempt missing",
            extra={"patch_attempt_id": patch_attempt_id, "correlation_id": correlation_id},
        )
        return
    repo = await db[COLLECTION_REPOSITORIES].find_one({"_id": patch["repository_id"]})
    if not repo:
        logger.warning(
            "pipeline_runner: repository missing",
            extra={"repository_id": patch["repository_id"], "correlation_id": correlation_id},
        )
        return

    project_id = repo.get("gitlab_project_id") or repo["_id"]
    default_branch = repo.get("default_branch", "main")
    branch = patch["branch_name"]
    manifest_path = patch["manifest_path"]
    manifest_content = patch["manifest_content"]
    attempt_number = patch.get("attempt_number", 1)

    try:
        await client.create_branch(project_id, branch=branch, ref=default_branch)
        await client.commit_files(
            project_id,
            branch=branch,
            message=patch["patch_summary"],
            files=[CommitFile(path=manifest_path, content=manifest_content)],
        )
        snapshot = await client.trigger_pipeline(project_id, ref=branch)
    except Exception as err:  # noqa: BLE001 — propagate as patch failure
        logger.exception(
            "GitLab branch/commit/pipeline trigger failed",
            extra={
                "patch_attempt_id": patch_attempt_id,
                "correlation_id": correlation_id,
                "error": str(err),
            },
        )
        await db[COLLECTION_PATCH_ATTEMPTS].update_one(
            {"_id": patch_attempt_id},
            {"$set": {"status": PatchStatus.FAILED.value, "updated_at": datetime.now(timezone.utc)}},
        )
        return

    pipeline_run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await db[COLLECTION_PIPELINE_RUNS].insert_one(
        {
            "_id": pipeline_run_id,
            "repository_id": patch["repository_id"],
            "patch_attempt_id": patch_attempt_id,
            "gitlab_pipeline_id": snapshot.pipeline_id,
            "status": PipelineStatus.RUNNING.value,
            "duration_seconds": 0,
            "failed_stage": None,
            "failure_summary": None,
            "logs_url": snapshot.logs_url,
            "retry_attempted": attempt_number > 1,
            "correlation_id": correlation_id,
            "created_at": now,
            "updated_at": now,
            "created_by": "gitlab_integration",
            "version": 1,
        }
    )
    await db[COLLECTION_PATCH_ATTEMPTS].update_one(
        {"_id": patch_attempt_id},
        {"$set": {"status": PatchStatus.VALIDATING.value, "updated_at": now}},
    )

    await publisher.publish(
        BaseEvent(
            event_type="ci.started",
            source_service="gitlab_integration",
            correlation_id=correlation_id,
            payload=CiStartedPayload(
                pipeline_run_id=pipeline_run_id,
                patch_attempt_id=patch_attempt_id,
                repository_id=patch["repository_id"],
                gitlab_pipeline_id=snapshot.pipeline_id,
                branch_name=branch,
            ).model_dump(),
        )
    )

    final = await _poll_until_done(
        client=client,
        project_id=project_id,
        pipeline_id=snapshot.pipeline_id,
        poll_interval=poll_interval,
        poll_timeout=poll_timeout,
    )

    end = datetime.now(timezone.utc)
    duration = (end - now).total_seconds()
    if final.status == "success":
        await _on_pipeline_passed(
            db,
            publisher,
            patch=patch,
            pipeline_run_id=pipeline_run_id,
            snapshot=final,
            duration=duration,
            correlation_id=correlation_id,
        )
    else:
        await _on_pipeline_failed(
            db,
            publisher,
            patch=patch,
            pipeline_run_id=pipeline_run_id,
            snapshot=final,
            duration=duration,
            attempt_number=attempt_number,
            correlation_id=correlation_id,
        )


async def _poll_until_done(
    *,
    client: GitLabClient,
    project_id: str,
    pipeline_id: str,
    poll_interval: float,
    poll_timeout: float,
):
    deadline = asyncio.get_event_loop().time() + poll_timeout
    while True:
        snapshot = await client.get_pipeline(project_id, pipeline_id)
        if snapshot.status in ("success", "failed", "canceled"):
            return snapshot
        if asyncio.get_event_loop().time() > deadline:
            snapshot.status = "failed"
            snapshot.failed_stage = snapshot.failed_stage or "timeout"
            snapshot.raw_logs = (snapshot.raw_logs or "") + "\n[poll timeout]"
            return snapshot
        await asyncio.sleep(poll_interval)


async def _on_pipeline_passed(
    db,
    publisher: RedisStreamPublisher,
    *,
    patch: dict,
    pipeline_run_id: str,
    snapshot,
    duration: float,
    correlation_id: str,
) -> None:
    now = datetime.now(timezone.utc)
    await db[COLLECTION_PIPELINE_RUNS].update_one(
        {"_id": pipeline_run_id},
        {
            "$set": {
                "status": PipelineStatus.PASSED.value,
                "duration_seconds": duration,
                "updated_at": now,
            }
        },
    )
    await db[COLLECTION_PATCH_ATTEMPTS].update_one(
        {"_id": patch["_id"]},
        {"$set": {"status": PatchStatus.VALIDATED.value, "updated_at": now}},
    )
    await publisher.publish(
        BaseEvent(
            event_type="pipeline.completed",
            source_service="gitlab_integration",
            correlation_id=correlation_id,
            payload={
                "pipeline_run_id": pipeline_run_id,
                "repository_id": patch["repository_id"],
                "status": "passed",
                "failed_stage": None,
            },
        )
    )
    await publisher.publish(
        BaseEvent(
            event_type="patch.validated",
            source_service="gitlab_integration",
            correlation_id=correlation_id,
            payload=PatchValidatedPayload(
                patch_attempt_id=patch["_id"],
                repository_id=patch["repository_id"],
                vulnerability_id=patch["vulnerability_id"],
                branch_name=patch["branch_name"],
                pipeline_run_id=pipeline_run_id,
            ).model_dump(),
        )
    )
    logger.info(
        "Pipeline passed — patch validated",
        extra={
            "patch_attempt_id": patch["_id"],
            "pipeline_run_id": pipeline_run_id,
            "correlation_id": correlation_id,
        },
    )


async def _on_pipeline_failed(
    db,
    publisher: RedisStreamPublisher,
    *,
    patch: dict,
    pipeline_run_id: str,
    snapshot,
    duration: float,
    attempt_number: int,
    correlation_id: str,
) -> None:
    now = datetime.now(timezone.utc)
    failure_summary = _summarize_failure(snapshot.raw_logs or "")
    await db[COLLECTION_PIPELINE_RUNS].update_one(
        {"_id": pipeline_run_id},
        {
            "$set": {
                "status": PipelineStatus.FAILED.value,
                "duration_seconds": duration,
                "failed_stage": snapshot.failed_stage or "unknown",
                "failure_summary": failure_summary,
                "logs_url": snapshot.logs_url,
                "updated_at": now,
            }
        },
    )
    await db[COLLECTION_PATCH_ATTEMPTS].update_one(
        {"_id": patch["_id"]},
        {"$set": {"status": PatchStatus.FAILED.value, "updated_at": now}},
    )
    await publisher.publish(
        BaseEvent(
            event_type="pipeline.completed",
            source_service="gitlab_integration",
            correlation_id=correlation_id,
            payload={
                "pipeline_run_id": pipeline_run_id,
                "repository_id": patch["repository_id"],
                "status": "failed",
                "failed_stage": snapshot.failed_stage or "unknown",
            },
        )
    )
    await publisher.publish(
        BaseEvent(
            event_type="ci.failed",
            source_service="gitlab_integration",
            correlation_id=correlation_id,
            payload=CiFailedPayload(
                pipeline_run_id=pipeline_run_id,
                patch_attempt_id=patch["_id"],
                repository_id=patch["repository_id"],
                gitlab_pipeline_id=snapshot.pipeline_id,
                failed_stage=snapshot.failed_stage or "unknown",
                failure_summary=failure_summary,
                logs_url=snapshot.logs_url,
                attempt_number=attempt_number,
            ).model_dump(),
        )
    )
    logger.info(
        "Pipeline failed — ci.failed emitted",
        extra={
            "patch_attempt_id": patch["_id"],
            "pipeline_run_id": pipeline_run_id,
            "failed_stage": snapshot.failed_stage,
            "correlation_id": correlation_id,
        },
    )


def _summarize_failure(logs: str, limit: int = 280) -> str:
    if not logs:
        return "Pipeline failed (no logs available)"
    interesting = [
        line.strip()
        for line in logs.splitlines()
        if any(tag in line for tag in ("Error", "ERROR", "FAILED", "Traceback", "TypeError", "ImportError"))
    ]
    if not interesting:
        interesting = [line.strip() for line in logs.splitlines() if line.strip()]
    summary = " | ".join(interesting[:3]) or "Pipeline failed"
    return summary[:limit]
