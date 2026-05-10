from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.utils.mongo import init_db, close_db
from shared.utils.redis_streams import get_redis, close_redis
from shared.logging import get_logger
from .config import settings
from .routes.health import router as health_router
from .routes.vulnerabilities import router as vuln_router
from .routes.repositories import router as repo_router
from .routes.remediations import router as remediation_router
from .routes.pipelines import router as pipeline_router
from .routes.merge_requests import router as mr_router
from .routes.events import router as events_router

logger = get_logger(settings.service_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting api_gateway", extra={"port": settings.service_port})
    await init_db(settings.mongo_uri)
    await get_redis(settings.redis_url)
    yield
    await close_db()
    await close_redis()
    logger.info("api_gateway stopped")


app = FastAPI(
    title="DependencyMedic API",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(health_router, prefix=PREFIX)
app.include_router(vuln_router, prefix=PREFIX)
app.include_router(repo_router, prefix=PREFIX)
app.include_router(remediation_router, prefix=PREFIX)
app.include_router(pipeline_router, prefix=PREFIX)
app.include_router(mr_router, prefix=PREFIX)
app.include_router(events_router, prefix=PREFIX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.api_gateway.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True,
    )
