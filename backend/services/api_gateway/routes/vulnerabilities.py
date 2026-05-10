from fastapi import APIRouter, Query
from shared.schemas.response import APIResponse
from shared.utils.mongo import get_database
from shared.constants import COLLECTION_VULNERABILITIES

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


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
