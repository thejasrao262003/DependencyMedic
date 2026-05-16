"""Publishes vuln.assessed and vuln.scored events to Redis Streams."""
from shared.utils.redis_streams import RedisStreamPublisher, get_redis
from shared.events.base import BaseEvent
from shared.events.vuln_events import VulnAssessedPayload, VulnScoredPayload
from shared.enums.severity import Severity
from shared.constants import STREAM_VULN_ASSESSED, STREAM_VULN_SCORED
from shared.logging import get_logger

logger = get_logger("reachability_analysis.producer")


class ReachabilityProducer:
    _publisher: RedisStreamPublisher | None = None

    async def _get_publisher(self) -> RedisStreamPublisher:
        if self._publisher is None:
            redis = await get_redis()
            self._publisher = RedisStreamPublisher(redis, "reachability_analysis")
        return self._publisher

    async def publish_assessed(
        self,
        *,
        vulnerability_id: str,
        repository_id: str,
        reachable: bool,
        confidence_score: float,
        evidence_count: int,
        correlation_id: str,
    ) -> str:
        publisher = await self._get_publisher()
        payload = VulnAssessedPayload(
            vulnerability_id=vulnerability_id,
            repository_id=repository_id,
            reachable=reachable,
            confidence_score=confidence_score,
            evidence_count=evidence_count,
        )
        event = BaseEvent(
            event_type=STREAM_VULN_ASSESSED,
            source_service="reachability_analysis",
            correlation_id=correlation_id,
            payload=payload.model_dump(),
        )
        msg_id = await publisher.publish(event)
        logger.info(
            "Published vuln.assessed",
            extra={
                "vulnerability_id": vulnerability_id,
                "repository_id": repository_id,
                "reachable": reachable,
                "confidence_score": confidence_score,
                "correlation_id": correlation_id,
            },
        )
        return msg_id

    async def publish_scored(
        self,
        *,
        vulnerability_id: str,
        repository_id: str,
        risk_score: int,
        risk_level: str,
        recommended_action: str,
        correlation_id: str,
    ) -> str:
        publisher = await self._get_publisher()
        payload = VulnScoredPayload(
            vulnerability_id=vulnerability_id,
            repository_id=repository_id,
            risk_score=risk_score,
            risk_level=Severity(risk_level),
            recommended_action=recommended_action,
        )
        event = BaseEvent(
            event_type=STREAM_VULN_SCORED,
            source_service="reachability_analysis",
            correlation_id=correlation_id,
            payload=payload.model_dump(),
        )
        msg_id = await publisher.publish(event)
        logger.info(
            "Published vuln.scored",
            extra={
                "vulnerability_id": vulnerability_id,
                "repository_id": repository_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "correlation_id": correlation_id,
            },
        )
        return msg_id
