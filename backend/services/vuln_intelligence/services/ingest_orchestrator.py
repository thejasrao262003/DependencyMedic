import uuid
from dataclasses import dataclass, field

from .nvd_ingestion import NVDIngestionService
from .osv_ingestion import OSVIngestionService
from .vuln_store import VulnStore
from .repo_matcher import RepoMatcher
from ..producers.vuln_producer import VulnProducer
from shared.constants import STREAM_VULN_DISCOVERED, STREAM_VULN_MATCHED
from shared.logging import get_logger

logger = get_logger("vuln_intelligence.orchestrator")


@dataclass
class IngestResult:
    total_fetched: int = 0
    new_stored: int = 0
    updated: int = 0
    events_published: int = 0
    matched_published: int = 0
    errors: list[str] = field(default_factory=list)


class IngestOrchestrator:
    def __init__(self, nvd_api_key: str | None = None):
        self.nvd = NVDIngestionService(api_key=nvd_api_key)
        self.osv = OSVIngestionService()
        self.store = VulnStore()
        self.producer = VulnProducer()
        self.matcher = RepoMatcher()

    async def run(
        self,
        days_back: int = 30,
        severities: list[str] | None = None,
        extra_packages: list[dict] | None = None,
    ) -> IngestResult:
        result = IngestResult()
        correlation_id = str(uuid.uuid4())

        logger.info(
            "Ingestion started",
            extra={
                "days_back": days_back,
                "severities": severities,
                "extra_packages": len(extra_packages or []),
                "correlation_id": correlation_id,
            },
        )

        # 1. Fetch from NVD by date + severity
        nvd_vulns = await self.nvd.fetch_recent_cves(
            days_back=days_back, severities=severities
        )
        result.total_fetched += len(nvd_vulns)

        # 2. Fetch from OSV by specific packages (optional)
        osv_vulns: list[dict] = []
        if extra_packages:
            osv_vulns = await self.osv.fetch_vulns_for_packages(extra_packages)
            result.total_fetched += len(osv_vulns)

        # 3. Merge: OSV package data enriches NVD entries where available
        # Only use the batch query results — no per-CVE individual OSV calls
        # (most recent CVEs are not yet indexed in OSV)
        osv_by_cve = {v["cve_id"]: v for v in osv_vulns}
        nvd_cve_ids = {v["cve_id"] for v in nvd_vulns}

        all_vulns = list(nvd_vulns)
        # Append OSV-only vulns not already covered by NVD
        for v in osv_vulns:
            if v["cve_id"] not in nvd_cve_ids:
                all_vulns.append(v)

        # Merge OSV package data into NVD entries where we have it
        for vuln in all_vulns:
            cve_id = vuln["cve_id"]
            if not vuln.get("affected_packages") and cve_id in osv_by_cve:
                vuln["affected_packages"] = osv_by_cve[cve_id].get("affected_packages", [])

        # 4. Store + publish events for new vulns
        for vuln in all_vulns:
            try:
                vuln_id, is_new = await self.store.upsert_vulnerability(vuln)

                if is_new:
                    result.new_stored += 1
                    await self.producer.publish_discovered(
                        vuln_id=vuln_id,
                        cve_id=vuln["cve_id"],
                        severity=vuln["severity"],
                        source=vuln["source"],
                        summary=vuln["summary"],
                        correlation_id=correlation_id,
                    )
                    await self.store.log_event(
                        event_type=STREAM_VULN_DISCOVERED,
                        correlation_id=correlation_id,
                        payload={
                            "vulnerability_id": vuln_id,
                            "cve_id": vuln["cve_id"],
                            "severity": vuln["severity"],
                            "source": vuln["source"],
                            "summary": vuln["summary"],
                        },
                    )
                    result.events_published += 1

                    # Match repos and publish vuln.matched if any are affected
                    affected_packages = vuln.get("affected_packages", [])
                    if affected_packages:
                        repo_ids = await self.matcher.find_affected_repos(
                            affected_packages=affected_packages,
                            vuln_id=vuln_id,
                            correlation_id=correlation_id,
                        )
                        if repo_ids:
                            await self.producer.publish_matched(
                                vuln_id=vuln_id,
                                cve_id=vuln["cve_id"],
                                repository_ids=repo_ids,
                                affected_packages=[
                                    p["name"] for p in affected_packages if p.get("name")
                                ],
                                correlation_id=correlation_id,
                            )
                            await self.store.log_event(
                                event_type=STREAM_VULN_MATCHED,
                                correlation_id=correlation_id,
                                payload={
                                    "vulnerability_id": vuln_id,
                                    "cve_id": vuln["cve_id"],
                                    "repository_ids": repo_ids,
                                    "affected_packages": [
                                        p["name"]
                                        for p in affected_packages
                                        if p.get("name")
                                    ],
                                },
                            )
                            result.matched_published += 1
                else:
                    result.updated += 1

            except Exception as exc:
                cve_id = vuln.get("cve_id", "unknown")
                logger.error(
                    "Failed to process vuln",
                    extra={"cve_id": cve_id, "error": str(exc)},
                )
                result.errors.append(f"{cve_id}: {exc}")

        logger.info(
            "Ingestion complete",
            extra={
                "total_fetched": result.total_fetched,
                "new_stored": result.new_stored,
                "updated": result.updated,
                "events_published": result.events_published,
                "matched_published": result.matched_published,
                "errors": len(result.errors),
                "correlation_id": correlation_id,
            },
        )
        return result
