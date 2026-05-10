from fastapi import APIRouter, Query
from shared.schemas.response import APIResponse
from shared.utils.mongo import get_database
from shared.constants import COLLECTION_MERGE_REQUESTS

router = APIRouter(prefix="/merge-requests", tags=["merge-requests"])


@router.get("", response_model=APIResponse)
async def list_merge_requests(
    status: str | None = Query(None),
    repository_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    db = get_database()
    query: dict = {}
    if status:
        query["status"] = status
    if repository_id:
        query["repository_id"] = repository_id

    skip = (page - 1) * limit
    cursor = db[COLLECTION_MERGE_REQUESTS].find(query).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    for item in items:
        item["id"] = str(item.pop("_id"))
    return APIResponse.ok(items)


@router.get("/{merge_request_id}", response_model=APIResponse)
async def get_merge_request(merge_request_id: str):
    db = get_database()
    doc = await db[COLLECTION_MERGE_REQUESTS].find_one({"_id": merge_request_id})
    if not doc:
        return APIResponse.fail("NOT_FOUND", f"Merge request {merge_request_id} not found")
    doc["id"] = str(doc.pop("_id"))
    return APIResponse.ok(doc)


@router.post("/{merge_request_id}/approve", response_model=APIResponse)
async def approve_merge_request(merge_request_id: str):
    db = get_database()
    result = await db[COLLECTION_MERGE_REQUESTS].update_one(
        {"_id": merge_request_id},
        {"$set": {"approved": True, "status": "approved"}},
    )
    if result.matched_count == 0:
        return APIResponse.fail("NOT_FOUND", f"Merge request {merge_request_id} not found")
    return APIResponse.ok({"approved": True})
