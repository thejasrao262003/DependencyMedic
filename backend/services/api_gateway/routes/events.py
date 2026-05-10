from fastapi import APIRouter, Query
from shared.schemas.response import APIResponse
from shared.utils.mongo import get_database
from shared.constants import COLLECTION_EVENTS

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=APIResponse)
async def list_events(
    event_type: str | None = Query(None),
    correlation_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    db = get_database()
    query: dict = {}
    if event_type:
        query["event_type"] = event_type
    if correlation_id:
        query["correlation_id"] = correlation_id

    skip = (page - 1) * limit
    cursor = (
        db[COLLECTION_EVENTS]
        .find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )
    items = await cursor.to_list(length=limit)
    for item in items:
        item["id"] = str(item.pop("_id"))
    total = await db[COLLECTION_EVENTS].count_documents(query)
    return APIResponse.ok({"items": items, "total": total})
