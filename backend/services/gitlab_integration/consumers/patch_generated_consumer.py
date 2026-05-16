"""Consume patch.generated and run the full GitLab pipeline orchestration."""

from __future__ import annotations

import asyncio
from typing import Any

from shared.constants import STREAM_PATCH_GENERATED
from shared.logging import get_logger
from shared.utils.redis_streams import RedisStreamConsumer, RedisStreamPublisher

from ..clients.protocol import GitLabClient
from ..services.pipeline_runner import run_patch_pipeline

logger = get_logger("gitlab_integration.patch_generated_consumer")


def make_consumer_task(
    redis,
    publisher: RedisStreamPublisher,
    client: GitLabClient,
    *,
    poll_interval: float,
    poll_timeout: float,
    consumer_name: str = "gitlab-1",
) -> asyncio.Task:
    consumer = RedisStreamConsumer(
        redis=redis,
        stream_name=STREAM_PATCH_GENERATED,
        group_name="gitlab_integration",
        consumer_name=consumer_name,
    )

    async def _handler(event: dict[str, Any]) -> None:
        payload = event.get("payload") or {}
        patch_attempt_id = payload.get("patch_attempt_id")
        correlation_id = event.get("correlation_id", "")
        if not patch_attempt_id:
            logger.warning(
                "patch.generated missing patch_attempt_id",
                extra={"correlation_id": correlation_id},
            )
            return
        await run_patch_pipeline(
            client=client,
            publisher=publisher,
            patch_attempt_id=patch_attempt_id,
            correlation_id=correlation_id,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )

    async def _run() -> None:
        await consumer.consume(_handler)

    return asyncio.create_task(_run(), name="patch_generated_consumer")
