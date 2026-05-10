from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from ..constants import DB_NAME

_client: AsyncIOMotorClient | None = None


async def init_db(mongo_uri: str) -> None:
    global _client
    _client = AsyncIOMotorClient(mongo_uri)


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _client[DB_NAME]
