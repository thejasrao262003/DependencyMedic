from contextlib import asynccontextmanager
from fastapi import FastAPI

from shared.utils.mongo import init_db, close_db
from shared.utils.redis_streams import get_redis, close_redis
from shared.logging import get_logger
from .config import settings
from .api.health import router as health_router

logger = get_logger(settings.service_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting reachability_analysis service", extra={"port": settings.service_port})
    await init_db(settings.mongo_uri)
    await get_redis(settings.redis_url)
    yield
    await close_db()
    await close_redis()
    logger.info("reachability_analysis service stopped")


app = FastAPI(
    title="Reachability Analysis Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.reachability_analysis.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True,
    )
