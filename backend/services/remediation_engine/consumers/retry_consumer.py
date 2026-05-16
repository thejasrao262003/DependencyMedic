"""Consume patch.retry_requested and regenerate the patch.

For the MVP we only re-run the deterministic patch generator with an
incremented attempt_number — that produces a fresh branch name (`-attempt-2`)
which the mock GitLab client treats as a passing build. Real-world adjustment
strategies (pinning transitive deps, downgrading) plug in here later.
"""

from __future__ import annotations

import asyncio
from typing import Any

from shared.constants import MAX_RETRY_ATTEMPTS, STREAM_PATCH_RETRY_REQUESTED
from shared.logging import get_logger
from shared.utils.redis_streams import RedisStreamConsumer, RedisStreamPublisher

from ..services.patch_generator import PatchGenerationError, generate_patch

logger = get_logger("remediation_engine.retry_consumer")


async def handle_retry(
    event: dict[str, Any],
    publisher: RedisStreamPublisher,
) -> None:
    payload = event.get("payload") or {}
    correlation_id = event.get("correlation_id", "")
    repository_id = payload.get("repository_id")
    vulnerability_id = payload.get("vulnerability_id")
    attempt_number = int(payload.get("attempt_number", 2))
    retry_reason = payload.get("retry_reason")

    if attempt_number > MAX_RETRY_ATTEMPTS:
        logger.info(
            "Retry attempt exceeds max — skipping",
            extra={
                "attempt_number": attempt_number,
                "max_attempts": MAX_RETRY_ATTEMPTS,
                "correlation_id": correlation_id,
            },
        )
        return
    if not repository_id or not vulnerability_id:
        logger.warning(
            "patch.retry_requested missing ids",
            extra={"correlation_id": correlation_id},
        )
        return

    try:
        await generate_patch(
            repository_id=repository_id,
            vulnerability_id=vulnerability_id,
            correlation_id=correlation_id,
            publisher=publisher,
            attempt_number=attempt_number,
            retry_reason=retry_reason,
        )
    except PatchGenerationError as err:
        logger.warning(
            "Retry patch generation failed",
            extra={
                "repository_id": repository_id,
                "vulnerability_id": vulnerability_id,
                "attempt_number": attempt_number,
                "reason": str(err),
                "correlation_id": correlation_id,
            },
        )


def make_consumer_task(
    redis,
    publisher: RedisStreamPublisher,
    *,
    consumer_name: str = "remediation-retry-1",
) -> asyncio.Task:
    consumer = RedisStreamConsumer(
        redis=redis,
        stream_name=STREAM_PATCH_RETRY_REQUESTED,
        group_name="remediation_engine_retry",
        consumer_name=consumer_name,
    )

    async def _handler(event: dict[str, Any]) -> None:
        await handle_retry(event, publisher)

    async def _run() -> None:
        await consumer.consume(_handler)

    return asyncio.create_task(_run(), name="retry_consumer")
