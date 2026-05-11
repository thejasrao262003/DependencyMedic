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
from .clients.factory import make_client
from .config import settings
from .consumers.patch_generated_consumer import (
    make_consumer_task as make_patch_generated_task,
)
from .consumers.patch_validated_consumer import (
    make_consumer_task as make_patch_validated_task,
)

logger = get_logger(settings.service_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting gitlab_integration service",
        extra={
            "port": settings.service_port,
            "mode": "live" if settings.gitlab_token else "mock",
        },
    )
    await init_db(settings.mongo_uri)
    redis = await get_redis(settings.redis_url)
    publisher = RedisStreamPublisher(redis=redis, service_name=settings.service_name)
    client = make_client(gitlab_url=settings.gitlab_url, gitlab_token=settings.gitlab_token)
    app.state.publisher = publisher
    app.state.gitlab_client = client

    tasks = [
        make_patch_generated_task(
            redis,
            publisher,
            client,
            poll_interval=settings.pipeline_poll_interval_seconds,
            poll_timeout=settings.pipeline_poll_max_seconds,
        ),
        make_patch_validated_task(redis, publisher, client),
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
        await client.aclose()
        await close_db()
        await close_redis()
        logger.info("gitlab_integration service stopped")


app = FastAPI(
    title="GitLab Integration Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.gitlab_integration.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True,
    )
