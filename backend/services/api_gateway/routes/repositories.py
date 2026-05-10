from fastapi import APIRouter, Query
from pydantic import BaseModel
from shared.schemas.response import APIResponse
from shared.utils.mongo import get_database
from shared.constants import COLLECTION_REPOSITORIES, COLLECTION_RISK_ASSESSMENTS

router = APIRouter(prefix="/repositories", tags=["repositories"])


class RegisterRepoRequest(BaseModel):
    repo_url: str


@router.get("", response_model=APIResponse)
async def list_repositories(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    db = get_database()
    query: dict = {}
    if status:
        query["status"] = status

    skip = (page - 1) * limit
    cursor = db[COLLECTION_REPOSITORIES].find(query).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    for item in items:
        item["id"] = str(item.pop("_id"))
    return APIResponse.ok(items)


@router.post("", response_model=APIResponse, status_code=201)
async def register_repository(body: RegisterRepoRequest):
    return APIResponse.ok(
        {"repository_id": None, "message": "Repository registration not yet implemented"}
    )


@router.get("/{repository_id}/risks", response_model=APIResponse)
async def get_repository_risks(repository_id: str):
    db = get_database()
    cursor = db[COLLECTION_RISK_ASSESSMENTS].find({"repository_id": repository_id})
    items = await cursor.to_list(length=100)
    for item in items:
        item["id"] = str(item.pop("_id"))
    return APIResponse.ok(items)
