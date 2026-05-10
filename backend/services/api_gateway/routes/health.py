from fastapi import APIRouter
from shared.schemas.response import APIResponse
from shared.utils.mongo import get_database
from shared.utils.redis_streams import get_redis

router = APIRouter(tags=["health"])


@router.get("/health", response_model=APIResponse)
async def health():
    checks: dict[str, str] = {}

    try:
        db = get_database()
        await db.command("ping")
        checks["mongodb"] = "healthy"
    except Exception:
        checks["mongodb"] = "unhealthy"

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception:
        checks["redis"] = "unhealthy"

    all_healthy = all(v == "healthy" for v in checks.values())
    return APIResponse.ok({"status": "healthy" if all_healthy else "degraded", "services": checks})
