import uuid
from datetime import datetime, timezone

from shared.utils.mongo import get_database
from shared.constants import COLLECTION_VULNERABILITIES, COLLECTION_EVENTS
from shared.logging import get_logger

logger = get_logger("vuln_intelligence.store")


class VulnStore:
    async def upsert_vulnerability(self, vuln_dict: dict) -> tuple[str, bool]:
        """Upsert by cve_id. Returns (vuln_id, is_new)."""
        db = get_database()
        cve_id = vuln_dict["cve_id"]
        now = datetime.now(timezone.utc).isoformat()

        existing = await db[COLLECTION_VULNERABILITIES].find_one({"cve_id": cve_id})

        if existing:
            vuln_id = str(existing["_id"])
            updates: dict = {
                "updated_at": now,
                "version": existing.get("version", 1) + 1,
            }
            # Only overwrite package data if we got better data
            if vuln_dict.get("affected_packages"):
                updates["affected_packages"] = vuln_dict["affected_packages"]
            if vuln_dict.get("cvss_score") is not None and existing.get("cvss_score") is None:
                updates["cvss_score"] = vuln_dict["cvss_score"]
            if vuln_dict.get("epss_score") is not None and existing.get("epss_score") is None:
                updates["epss_score"] = vuln_dict["epss_score"]

            await db[COLLECTION_VULNERABILITIES].update_one(
                {"_id": existing["_id"]}, {"$set": updates}
            )
            return vuln_id, False

        vuln_id = str(uuid.uuid4())
        doc = {
            "_id": vuln_id,
            **vuln_dict,
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "created_by": "vuln_intelligence",
            "version": 1,
        }
        await db[COLLECTION_VULNERABILITIES].insert_one(doc)
        logger.info("Stored new vulnerability", extra={"cve_id": cve_id, "vuln_id": vuln_id})
        return vuln_id, True

    async def log_event(self, event_type: str, correlation_id: str, payload: dict) -> None:
        """Write event record to events collection for audit/replay."""
        db = get_database()
        now = datetime.now(timezone.utc).isoformat()
        await db[COLLECTION_EVENTS].insert_one({
            "_id": str(uuid.uuid4()),
            "event_type": event_type,
            "source_service": "vuln_intelligence",
            "correlation_id": correlation_id,
            "payload": payload,
            "timestamp": now,
            "created_at": now,
            "updated_at": now,
            "created_by": "vuln_intelligence",
            "version": 1,
        })
