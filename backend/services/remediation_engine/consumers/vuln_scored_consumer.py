"""Consume vuln.scored and trigger deterministic patch generation.

Only acts on assessments at risk_level >= medium (per workflows.md §3) and
where reachability has actually flagged the vulnerability as exploitable.
"""

from __future__ import annotations

import asyncio
from typing import Any

from shared.constants import STREAM_VULN_SCORED
from shared.enums import Severity
from shared.logging import get_logger
from shared.utils.redis_streams import RedisStreamConsumer, RedisStreamPublisher

from ..services.patch_generator import PatchGenerationError, generate_patch

logger = get_logger("remediation_engine.vuln_scored_consumer")

_ACTIONABLE = {Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL}


def _is_actionable(risk_level: str) -> bool:
    try:
        return Severity(risk_level.lower()) in _ACTIONABLE
    except ValueError:
        return False


async def handle_vuln_scored(
    event: dict[str, Any], publisher: RedisStreamPublisher
) -> None:
    payload = event.get("payload") or {}
    correlation_id = event.get("correlation_id", "")
    risk_level = str(payload.get("risk_level") or "")
    if not _is_actionable(risk_level):
        logger.info(
            "Skipping vuln.scored — risk below threshold",
            extra={"risk_level": risk_level, "correlation_id": correlation_id},
        )
        return

    repository_id = payload.get("repository_id")
    vulnerability_id = payload.get("vulnerability_id")
    if not repository_id or not vulnerability_id:
        logger.warning(
            "vuln.scored missing repository_id or vulnerability_id",
            extra={"correlation_id": correlation_id},
        )
        return

    try:
        await generate_patch(
            repository_id=repository_id,
            vulnerability_id=vulnerability_id,
            correlation_id=correlation_id,
            publisher=publisher,
            attempt_number=1,
        )
    except PatchGenerationError as err:
        logger.warning(
            "Patch generation failed",
            extra={
                "repository_id": repository_id,
                "vulnerability_id": vulnerability_id,
                "reason": str(err),
                "correlation_id": correlation_id,
            },
        )


def make_consumer_task(
    redis, publisher: RedisStreamPublisher, *, consumer_name: str = "remediation-1"
) -> asyncio.Task:
    consumer = RedisStreamConsumer(
        redis=redis,
        stream_name=STREAM_VULN_SCORED,
        group_name="remediation_engine",
        consumer_name=consumer_name,
    )

    async def _handler(event: dict[str, Any]) -> None:
        await handle_vuln_scored(event, publisher)

    async def _run() -> None:
        await consumer.consume(_handler)

    return asyncio.create_task(_run(), name="vuln_scored_consumer")
