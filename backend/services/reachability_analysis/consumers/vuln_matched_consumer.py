"""
Consume vuln.matched events and run reachability analysis for each repo.

For each (vulnerability_id, repository_id) pair in the event, the agent:
  1. Loads the vulnerability + dependency snapshot from MongoDB
  2. Runs deterministic reachability analysis
  3. Persists a risk_assessment document
  4. Publishes vuln.assessed + vuln.scored events

Idempotency: handled by upsert on (vulnerability_id, repository_id) in
risk_assessments. Re-processing the same event overwrites the assessment
with fresh data — safe for demo replay.
"""
from __future__ import annotations

import asyncio
from typing import Any

from shared.constants import STREAM_VULN_MATCHED, STREAM_VULN_ASSESSED, STREAM_VULN_SCORED
from shared.logging import get_logger
from shared.utils.redis_streams import RedisStreamConsumer, RedisStreamPublisher

from ..agents.reachability_agent import run_reachability_agent
from ..producers.reachability_producer import ReachabilityProducer
from ..services.reachability_store import ReachabilityStore

logger = get_logger("reachability_analysis.vuln_matched_consumer")


async def handle_vuln_matched(
    event: dict[str, Any],
    producer: ReachabilityProducer,
    store: ReachabilityStore,
    gemini_api_key: str = "",
) -> None:
    payload = event.get("payload") or {}
    correlation_id = event.get("correlation_id", "")

    vulnerability_id: str = payload.get("vulnerability_id", "")
    repository_ids: list[str] = payload.get("repository_ids", [])

    if not vulnerability_id or not repository_ids:
        logger.warning(
            "vuln.matched missing required fields",
            extra={"correlation_id": correlation_id},
        )
        return

    logger.info(
        "Processing vuln.matched",
        extra={
            "vulnerability_id": vulnerability_id,
            "repository_count": len(repository_ids),
            "correlation_id": correlation_id,
        },
    )

    for repository_id in repository_ids:
        try:
            result = await run_reachability_agent(
                vulnerability_id=vulnerability_id,
                repository_id=repository_id,
                correlation_id=correlation_id,
                gemini_api_key=gemini_api_key,
            )

            # Persist
            await store.upsert_risk_assessment(
                vulnerability_id=result.vulnerability_id,
                repository_id=result.repository_id,
                reachable=result.reachable,
                confidence_score=result.confidence_score,
                risk_score=result.risk_score,
                risk_level=result.risk_level,
                evidence=result.evidence,
                analysis_summary=result.analysis_summary,
                recommended_action=result.recommended_action,
                correlation_id=correlation_id,
            )
            await store.log_event(
                STREAM_VULN_ASSESSED,
                correlation_id,
                {
                    "vulnerability_id": result.vulnerability_id,
                    "repository_id": result.repository_id,
                    "reachable": result.reachable,
                    "confidence_score": result.confidence_score,
                    "evidence_count": result.evidence_count,
                },
            )

            # Publish vuln.assessed
            await producer.publish_assessed(
                vulnerability_id=result.vulnerability_id,
                repository_id=result.repository_id,
                reachable=result.reachable,
                confidence_score=result.confidence_score,
                evidence_count=result.evidence_count,
                correlation_id=correlation_id,
            )

            # Publish vuln.scored (remediation_engine picks this up)
            await producer.publish_scored(
                vulnerability_id=result.vulnerability_id,
                repository_id=result.repository_id,
                risk_score=result.risk_score,
                risk_level=result.risk_level,
                recommended_action=result.recommended_action,
                correlation_id=correlation_id,
            )
            await store.log_event(
                STREAM_VULN_SCORED,
                correlation_id,
                {
                    "vulnerability_id": result.vulnerability_id,
                    "repository_id": result.repository_id,
                    "risk_score": result.risk_score,
                    "risk_level": result.risk_level,
                    "recommended_action": result.recommended_action,
                },
            )

        except Exception as exc:
            logger.error(
                "Reachability analysis failed for repo",
                extra={
                    "vulnerability_id": vulnerability_id,
                    "repository_id": repository_id,
                    "error": str(exc),
                    "correlation_id": correlation_id,
                },
            )


def make_consumer_task(
    redis,
    producer: ReachabilityProducer,
    store: ReachabilityStore,
    *,
    gemini_api_key: str = "",
    consumer_name: str = "reachability-1",
) -> asyncio.Task:
    consumer = RedisStreamConsumer(
        redis=redis,
        stream_name=STREAM_VULN_MATCHED,
        group_name="reachability_analysis",
        consumer_name=consumer_name,
    )

    async def _handler(event: dict[str, Any]) -> None:
        await handle_vuln_matched(event, producer, store, gemini_api_key)

    async def _run() -> None:
        await consumer.consume(_handler)

    return asyncio.create_task(_run(), name="vuln_matched_consumer")
