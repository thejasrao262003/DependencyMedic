from shared.utils.redis_streams import RedisStreamPublisher, get_redis
from shared.events.base import BaseEvent
from shared.events.vuln_events import VulnDiscoveredPayload, VulnMatchedPayload
from shared.enums.severity import Severity
from shared.constants import STREAM_VULN_DISCOVERED, STREAM_VULN_MATCHED
from shared.logging import get_logger

logger = get_logger("vuln_intelligence.producer")


class VulnProducer:
    _publisher: RedisStreamPublisher | None = None

    async def _publisher_instance(self) -> RedisStreamPublisher:
        if self._publisher is None:
            redis = await get_redis()
            self._publisher = RedisStreamPublisher(redis, "vuln_intelligence")
        return self._publisher

    async def publish_discovered(
        self,
        *,
        vuln_id: str,
        cve_id: str,
        severity: str,
        source: str,
        summary: str,
        correlation_id: str,
    ) -> str:
        publisher = await self._publisher_instance()
        payload = VulnDiscoveredPayload(
            vulnerability_id=vuln_id,
            cve_id=cve_id,
            severity=Severity(severity),
            source=source,
            summary=summary,
        )
        event = BaseEvent(
            event_type=STREAM_VULN_DISCOVERED,
            source_service="vuln_intelligence",
            correlation_id=correlation_id,
            payload=payload.model_dump(),
        )
        msg_id = await publisher.publish(event)
        logger.info(
            "Published vuln.discovered",
            extra={"cve_id": cve_id, "vuln_id": vuln_id, "correlation_id": correlation_id},
        )
        return msg_id

    async def publish_matched(
        self,
        *,
        vuln_id: str,
        cve_id: str,
        repository_ids: list[str],
        affected_packages: list[str],
        correlation_id: str,
    ) -> str:
        publisher = await self._publisher_instance()
        payload = VulnMatchedPayload(
            vulnerability_id=vuln_id,
            cve_id=cve_id,
            repository_ids=repository_ids,
            affected_packages=affected_packages,
        )
        event = BaseEvent(
            event_type=STREAM_VULN_MATCHED,
            source_service="vuln_intelligence",
            correlation_id=correlation_id,
            payload=payload.model_dump(),
        )
        msg_id = await publisher.publish(event)
        logger.info(
            "Published vuln.matched",
            extra={
                "cve_id": cve_id,
                "repository_count": len(repository_ids),
                "correlation_id": correlation_id,
            },
        )
        return msg_id
