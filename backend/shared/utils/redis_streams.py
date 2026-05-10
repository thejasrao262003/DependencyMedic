import asyncio
import json
from typing import Any, Callable, Awaitable
import redis.asyncio as aioredis

from ..events.base import BaseEvent

_redis_client: aioredis.Redis | None = None


async def get_redis(redis_url: str | None = None) -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        if redis_url is None:
            raise RuntimeError("Redis not initialized. Call get_redis(url) first.")
        _redis_client = await aioredis.from_url(redis_url, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


class RedisStreamPublisher:
    def __init__(self, redis: aioredis.Redis, service_name: str):
        self.redis = redis
        self.service_name = service_name

    async def publish(self, event: BaseEvent) -> str:
        data = {"data": event.model_dump_json()}
        msg_id = await self.redis.xadd(event.event_type, data)
        return msg_id


class RedisStreamConsumer:
    def __init__(
        self,
        redis: aioredis.Redis,
        stream_name: str,
        group_name: str,
        consumer_name: str,
    ):
        self.redis = redis
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name

    async def ensure_group(self) -> None:
        try:
            await self.redis.xgroup_create(
                self.stream_name, self.group_name, id="0", mkstream=True
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def consume(
        self,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
        batch_size: int = 10,
        block_ms: int = 2000,
    ) -> None:
        await self.ensure_group()
        while True:
            try:
                messages = await self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={self.stream_name: ">"},
                    count=batch_size,
                    block=block_ms,
                )
                if not messages:
                    continue
                for _, entries in messages:
                    for msg_id, fields in entries:
                        try:
                            payload = json.loads(fields["data"])
                            await handler(payload)
                            await self.redis.xack(self.stream_name, self.group_name, msg_id)
                        except Exception:
                            pass
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)
