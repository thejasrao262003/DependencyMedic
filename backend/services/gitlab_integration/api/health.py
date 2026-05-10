from fastapi import APIRouter
from shared.schemas.response import APIResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=APIResponse)
async def health():
    return APIResponse.ok({"status": "healthy", "service": "gitlab_integration"})
