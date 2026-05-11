from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.logging import get_logger
from shared.utils.mongo import close_db, init_db
from shared.utils.redis_streams import (
    RedisStreamPublisher,
    close_redis,
    get_redis,
)

from .api.health import router as health_router
from .api.remediate import router as remediate_router
from .config import settings
from .consumers.vuln_scored_consumer import (
    make_consumer_task as make_vuln_scored_task,
)
from .consumers.ci_failed_consumer import (
    make_consumer_task as make_ci_failed_task,
)
from .consumers.retry_consumer import (
    make_consumer_task as make_retry_task,
)

logger = get_logger(settings.service_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting remediation_engine service",
        extra={"port": settings.service_port},
    )
    await init_db(settings.mongo_uri)
    redis = await get_redis(settings.redis_url)
    publisher = RedisStreamPublisher(redis=redis, service_name=settings.service_name)
    app.state.publisher = publisher

    tasks = [
        make_vuln_scored_task(redis, publisher),
        make_ci_failed_task(redis, publisher),
        make_retry_task(redis, publisher),
    ]
    app.state.background_tasks = tasks

    try:
        yield
    finally:
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except Exception:
                pass
        await close_db()
        await close_redis()
        logger.info("remediation_engine service stopped")


app = FastAPI(
    title="Remediation Engine Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(remediate_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.remediation_engine.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True,
    )
