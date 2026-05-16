"""Consume ci.failed, run the CI Failure Analysis Agent, decide retry vs escalation."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from shared.constants import (
    COLLECTION_PATCH_ATTEMPTS,
    MAX_RETRY_ATTEMPTS,
    STREAM_CI_FAILED,
)
from shared.enums import PatchStatus
from shared.events.base import BaseEvent
from shared.events.patch_events import PatchRetryRequestedPayload
from shared.logging import get_logger
from shared.utils.mongo import get_database
from shared.utils.redis_streams import RedisStreamConsumer, RedisStreamPublisher

from ..agents.ci_failure_agent import CiFailureAgent
from ..config import settings

logger = get_logger("remediation_engine.ci_failed_consumer")


async def handle_ci_failed(
    event: dict[str, Any],
    publisher: RedisStreamPublisher,
    agent: CiFailureAgent,
) -> None:
    payload = event.get("payload") or {}
    correlation_id = event.get("correlation_id", "")
    patch_attempt_id = payload.get("patch_attempt_id")
    pipeline_run_id = payload.get("pipeline_run_id")
    attempt_number = int(payload.get("attempt_number", 1))
    if not patch_attempt_id:
        logger.warning(
            "ci.failed missing patch_attempt_id",
            extra={"correlation_id": correlation_id},
        )
        return

    db = get_database()
    patch = await db[COLLECTION_PATCH_ATTEMPTS].find_one({"_id": patch_attempt_id})
    if not patch:
        logger.warning(
            "ci.failed for unknown patch_attempt",
            extra={"patch_attempt_id": patch_attempt_id, "correlation_id": correlation_id},
        )
        return

    # Pull logs through pipeline_runs failure_summary as a stand-in when the
    # raw trace isn't propagated on the event.
    logs = payload.get("failure_summary", "") or ""

    verdict = await agent.run(
        pipeline_run_id=pipeline_run_id or "",
        patch_attempt_id=patch_attempt_id,
        correlation_id=correlation_id,
        logs=logs,
    )

    next_attempt = attempt_number + 1
    if not verdict["retry_recommended"] or next_attempt > MAX_RETRY_ATTEMPTS:
        await db[COLLECTION_PATCH_ATTEMPTS].update_one(
            {"_id": patch_attempt_id},
            {
                "$set": {
                    "status": PatchStatus.ESCALATED.value,
                    "retry_reason": verdict["summary"],
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info(
            "Escalating patch — retry exhausted or not recommended",
            extra={
                "patch_attempt_id": patch_attempt_id,
                "attempt_number": attempt_number,
                "max_attempts": MAX_RETRY_ATTEMPTS,
                "correlation_id": correlation_id,
            },
        )
        return

    await publisher.publish(
        BaseEvent(
            event_type="patch.retry_requested",
            source_service="remediation_engine",
            correlation_id=correlation_id,
            payload=PatchRetryRequestedPayload(
                patch_attempt_id=patch_attempt_id,
                repository_id=patch["repository_id"],
                vulnerability_id=patch["vulnerability_id"],
                pipeline_run_id=pipeline_run_id or "",
                failure_type=verdict["failure_type"],
                retry_reason=verdict["summary"],
                attempt_number=next_attempt,
            ).model_dump(),
        )
    )
    logger.info(
        "patch.retry_requested emitted",
        extra={
            "patch_attempt_id": patch_attempt_id,
            "next_attempt": next_attempt,
            "failure_type": verdict["failure_type"],
            "correlation_id": correlation_id,
        },
    )


def make_consumer_task(
    redis,
    publisher: RedisStreamPublisher,
    *,
    consumer_name: str = "remediation-ci-1",
) -> asyncio.Task:
    consumer = RedisStreamConsumer(
        redis=redis,
        stream_name=STREAM_CI_FAILED,
        group_name="remediation_engine_ci",
        consumer_name=consumer_name,
    )
    agent = CiFailureAgent(gemini_api_key=settings.gemini_api_key)

    async def _handler(event: dict[str, Any]) -> None:
        await handle_ci_failed(event, publisher, agent)

    async def _run() -> None:
        await consumer.consume(_handler)

    return asyncio.create_task(_run(), name="ci_failed_consumer")
