from fastapi import APIRouter, Query
from shared.schemas.response import APIResponse
from shared.utils.mongo import get_database
from shared.constants import COLLECTION_PIPELINE_RUNS

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("", response_model=APIResponse)
async def list_pipelines(
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
    cursor = db[COLLECTION_PIPELINE_RUNS].find(query).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    for item in items:
        item["id"] = str(item.pop("_id"))
    return APIResponse.ok(items)


@router.get("/{pipeline_id}", response_model=APIResponse)
async def get_pipeline(pipeline_id: str):
    db = get_database()
    doc = await db[COLLECTION_PIPELINE_RUNS].find_one({"_id": pipeline_id})
    if not doc:
        return APIResponse.fail("NOT_FOUND", f"Pipeline {pipeline_id} not found")
    doc["id"] = str(doc.pop("_id"))
    return APIResponse.ok(doc)
