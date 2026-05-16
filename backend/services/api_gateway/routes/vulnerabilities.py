from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
import httpx

from shared.schemas.response import APIResponse
from shared.utils.mongo import get_database
from shared.constants import COLLECTION_VULNERABILITIES
from ..config import settings

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


class PackageQuery(BaseModel):
    name: str
    ecosystem: str


class IngestRequest(BaseModel):
    days_back: int = Field(default=30, ge=1, le=365)
    severities: list[str] = Field(default=["CRITICAL", "HIGH"])
    packages: list[PackageQuery] = Field(default=[])


@router.post("/ingest", response_model=APIResponse, status_code=202)
async def trigger_ingest(body: IngestRequest):
    """Proxy to vuln_intelligence — triggers CVE ingestion from NVD and OSV."""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(
                f"{settings.vuln_intelligence_url}/api/v1/ingest",
                json=body.model_dump(),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as exc:
        return APIResponse.fail("INGEST_ERROR", str(exc))
    except Exception as exc:
        return APIResponse.fail("INGEST_UNAVAILABLE", f"vuln_intelligence unreachable: {exc}")


@router.get("", response_model=APIResponse)
async def list_vulnerabilities(
    severity: str | None = Query(None),
    status: str | None = Query(None, description="active|resolved"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    db = get_database()
    query: dict = {}
    if severity:
        query["severity"] = severity
    if status:
        query["status"] = status

    skip = (page - 1) * limit
    cursor = db[COLLECTION_VULNERABILITIES].find(query).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await db[COLLECTION_VULNERABILITIES].count_documents(query)

    for item in items:
        item["id"] = str(item.pop("_id"))

    return APIResponse.ok({"items": items, "total": total, "page": page, "limit": limit})


@router.get("/{vulnerability_id}", response_model=APIResponse)
async def get_vulnerability(vulnerability_id: str):
    db = get_database()
    doc = await db[COLLECTION_VULNERABILITIES].find_one({"_id": vulnerability_id})
    if not doc:
        return APIResponse.fail("NOT_FOUND", f"Vulnerability {vulnerability_id} not found")
    doc["id"] = str(doc.pop("_id"))
    return APIResponse.ok(doc)


@router.post("/{vulnerability_id}/match", response_model=APIResponse)
async def trigger_match(vulnerability_id: str):
    """Proxy to vuln_intelligence — re-run repo matching for an existing vulnerability."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{settings.vuln_intelligence_url}/api/v1/match/{vulnerability_id}",
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as exc:
        return APIResponse.fail("MATCH_ERROR", str(exc))
    except Exception as exc:
        return APIResponse.fail("MATCH_UNAVAILABLE", f"vuln_intelligence unreachable: {exc}")
