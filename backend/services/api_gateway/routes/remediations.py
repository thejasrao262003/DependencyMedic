from fastapi import APIRouter, Query
from pydantic import BaseModel
from shared.schemas.response import APIResponse
from shared.utils.mongo import get_database
from shared.constants import COLLECTION_PATCH_ATTEMPTS

router = APIRouter(prefix="/remediations", tags=["remediations"])


class GenerateRemediationRequest(BaseModel):
    repository_id: str
    vulnerability_id: str


@router.post("/generate", response_model=APIResponse, status_code=202)
async def generate_remediation(body: GenerateRemediationRequest):
    return APIResponse.ok(
        {"patch_attempt_id": None, "status": "started", "message": "Remediation not yet implemented"}
    )


@router.get("", response_model=APIResponse)
async def list_remediations(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    db = get_database()
    query: dict = {}
    if status:
        query["status"] = status

    skip = (page - 1) * limit
    cursor = db[COLLECTION_PATCH_ATTEMPTS].find(query).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    for item in items:
        item["id"] = str(item.pop("_id"))
    return APIResponse.ok(items)


@router.get("/{patch_attempt_id}", response_model=APIResponse)
async def get_remediation(patch_attempt_id: str):
    db = get_database()
    doc = await db[COLLECTION_PATCH_ATTEMPTS].find_one({"_id": patch_attempt_id})
    if not doc:
        return APIResponse.fail("NOT_FOUND", f"Patch attempt {patch_attempt_id} not found")
    doc["id"] = str(doc.pop("_id"))
    return APIResponse.ok(doc)
