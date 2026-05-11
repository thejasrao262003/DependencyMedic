"""Consume patch.validated and open the remediation MR."""

from __future__ import annotations

import asyncio
from typing import Any

from shared.constants import STREAM_PATCH_VALIDATED
from shared.logging import get_logger
from shared.utils.redis_streams import RedisStreamConsumer, RedisStreamPublisher

from ..clients.protocol import GitLabClient
from ..services.mr_creator import create_remediation_mr

logger = get_logger("gitlab_integration.patch_validated_consumer")


def make_consumer_task(
    redis,
    publisher: RedisStreamPublisher,
    client: GitLabClient,
    *,
    consumer_name: str = "gitlab-mr-1",
) -> asyncio.Task:
    consumer = RedisStreamConsumer(
        redis=redis,
        stream_name=STREAM_PATCH_VALIDATED,
        group_name="gitlab_integration_mr",
        consumer_name=consumer_name,
    )

    async def _handler(event: dict[str, Any]) -> None:
        payload = event.get("payload") or {}
        patch_attempt_id = payload.get("patch_attempt_id")
        pipeline_run_id = payload.get("pipeline_run_id")
        correlation_id = event.get("correlation_id", "")
        if not patch_attempt_id:
            logger.warning(
                "patch.validated missing patch_attempt_id",
                extra={"correlation_id": correlation_id},
            )
            return
        await create_remediation_mr(
            client=client,
            publisher=publisher,
            patch_attempt_id=patch_attempt_id,
            pipeline_run_id=pipeline_run_id or "",
            correlation_id=correlation_id,
        )

    async def _run() -> None:
        await consumer.consume(_handler)

    return asyncio.create_task(_run(), name="patch_validated_consumer")
