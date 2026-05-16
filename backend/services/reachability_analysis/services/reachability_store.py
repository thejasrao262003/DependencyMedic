"""Persists risk_assessment results to MongoDB."""
import uuid
from datetime import datetime, timezone

from shared.utils.mongo import get_database
from shared.constants import COLLECTION_RISK_ASSESSMENTS, COLLECTION_EVENTS
from shared.logging import get_logger

logger = get_logger("reachability_analysis.store")


class ReachabilityStore:
    async def upsert_risk_assessment(
        self,
        *,
        vulnerability_id: str,
        repository_id: str,
        reachable: bool,
        confidence_score: float,
        risk_score: int,
        risk_level: str,
        evidence: list[dict],
        analysis_summary: str,
        recommended_action: str,
        correlation_id: str,
    ) -> str:
        """Upsert risk assessment for a (vulnerability_id, repository_id) pair."""
        db = get_database()
        now = datetime.now(timezone.utc).isoformat()
        assessment_id = str(uuid.uuid4())

        await db[COLLECTION_RISK_ASSESSMENTS].update_one(
            {"vulnerability_id": vulnerability_id, "repository_id": repository_id},
            {
                "$set": {
                    "vulnerability_id": vulnerability_id,
                    "repository_id": repository_id,
                    "reachable": reachable,
                    "confidence_score": confidence_score,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "evidence": evidence,
                    "analysis_summary": analysis_summary,
                    "recommended_action": recommended_action,
                    "assessed_by": "reachability_agent",
                    "correlation_id": correlation_id,
                    "updated_at": now,
                    "created_by": "reachability_analysis",
                    "version": 1,
                },
                "$setOnInsert": {
                    "_id": assessment_id,
                    "created_at": now,
                },
            },
            upsert=True,
        )
        logger.info(
            "Upserted risk assessment",
            extra={
                "vulnerability_id": vulnerability_id,
                "repository_id": repository_id,
                "risk_score": risk_score,
                "correlation_id": correlation_id,
            },
        )
        return assessment_id

    async def log_event(
        self, event_type: str, correlation_id: str, payload: dict
    ) -> None:
        db = get_database()
        now = datetime.now(timezone.utc).isoformat()
        await db[COLLECTION_EVENTS].insert_one(
            {
                "_id": str(uuid.uuid4()),
                "event_type": event_type,
                "source_service": "reachability_analysis",
                "correlation_id": correlation_id,
                "payload": payload,
                "timestamp": now,
                "created_at": now,
                "updated_at": now,
                "created_by": "reachability_analysis",
                "version": 1,
            }
        )
