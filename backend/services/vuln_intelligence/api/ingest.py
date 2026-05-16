from fastapi import APIRouter
from pydantic import BaseModel, Field

from shared.schemas.response import APIResponse
from shared.logging import get_logger
from ..services.ingest_orchestrator import IngestOrchestrator
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
        "errors": result.errors,
    })
