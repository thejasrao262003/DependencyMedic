import uuid
from fastapi import APIRouter
from pydantic import BaseModel, Field

from shared.schemas.response import APIResponse
from shared.logging import get_logger
from shared.utils.mongo import get_database
from shared.constants import COLLECTION_VULNERABILITIES, STREAM_VULN_MATCHED
from ..services.ingest_orchestrator import IngestOrchestrator
from ..services.repo_matcher import RepoMatcher
from ..services.vuln_store import VulnStore
from ..producers.vuln_producer import VulnProducer
from ..config import settings

router = APIRouter(tags=["ingest"])
logger = get_logger("vuln_intelligence.api.ingest")


class PackageQuery(BaseModel):
    name: str
    ecosystem: str


class IngestRequest(BaseModel):
    days_back: int = Field(default=30, ge=1, le=365)
    severities: list[str] = Field(default=["CRITICAL", "HIGH"])
    packages: list[PackageQuery] = Field(
        default=[],
        description="Optional extra packages to query in OSV (e.g. log4j-core/Maven)",
    )


@router.post("/ingest", response_model=APIResponse)
async def trigger_ingest(body: IngestRequest):
    """
    Trigger CVE ingestion from NVD and OSV.
    Fetches recent CVEs, stores new ones in MongoDB, and publishes vuln.discovered events.
    """
    orchestrator = IngestOrchestrator(nvd_api_key=settings.nvd_api_key or None)

    extra_packages = [p.model_dump() for p in body.packages]

    result = await orchestrator.run(
        days_back=body.days_back,
        severities=body.severities,
        extra_packages=extra_packages,
    )

    return APIResponse.ok({
        "total_fetched": result.total_fetched,
        "new_stored": result.new_stored,
        "updated": result.updated,
        "events_published": result.events_published,
        "matched_published": result.matched_published,
        "errors": result.errors,
    })


@router.post("/match/{vuln_id}", response_model=APIResponse)
async def trigger_match(vuln_id: str):
    """
    Re-run repo matching for an existing vulnerability and publish vuln.matched.
    Useful for seeded demo data or when new repos are added after initial ingestion.
    """
    db = get_database()
    doc = await db[COLLECTION_VULNERABILITIES].find_one({"_id": vuln_id})
    if not doc:
        return APIResponse.fail("NOT_FOUND", f"Vulnerability {vuln_id} not found")

    affected_packages = doc.get("affected_packages", [])
    if not affected_packages:
        return APIResponse.fail(
            "NO_PACKAGES",
            f"Vulnerability {vuln_id} has no affected_packages — cannot match repos",
        )

    correlation_id = str(uuid.uuid4())
    matcher = RepoMatcher()
    store = VulnStore()
    producer = VulnProducer()

    repo_ids = await matcher.find_affected_repos(
        affected_packages=affected_packages,
        vuln_id=vuln_id,
        correlation_id=correlation_id,
    )

    if not repo_ids:
        return APIResponse.ok({
            "vuln_id": vuln_id,
            "cve_id": doc.get("cve_id"),
            "matched_repos": [],
            "vuln_matched_published": False,
            "message": "No repos matched this vulnerability's affected packages",
        })

    await producer.publish_matched(
        vuln_id=vuln_id,
        cve_id=doc["cve_id"],
        repository_ids=repo_ids,
        affected_packages=[p["name"] for p in affected_packages if p.get("name")],
        correlation_id=correlation_id,
    )
    await store.log_event(
        event_type=STREAM_VULN_MATCHED,
        correlation_id=correlation_id,
        payload={
            "vulnerability_id": vuln_id,
            "cve_id": doc["cve_id"],
            "repository_ids": repo_ids,
        },
    )

    logger.info(
        "Manual match triggered",
        extra={"vuln_id": vuln_id, "repo_count": len(repo_ids), "correlation_id": correlation_id},
    )

    return APIResponse.ok({
        "vuln_id": vuln_id,
        "cve_id": doc.get("cve_id"),
        "matched_repos": repo_ids,
        "vuln_matched_published": True,
        "correlation_id": correlation_id,
    })
