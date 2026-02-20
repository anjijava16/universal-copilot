"""
core/redis_client.py — Async Redis Client Wrapper
===================================================
Thin async wrapper around redis.asyncio.
Provides connect/disconnect lifecycle and typed helpers.
All session, skill, agent state stored here.
"""

from __future__ import annotations  # defers annotation evaluation — fixes set[str] shadowed by self.set method

import redis.asyncio as aioredis
from redis.asyncio import Redis
from core.config import settings
import structlog

log = structlog.get_logger(__name__)


class RedisClient:
    """
    Async Redis client with explicit connect/disconnect.
    Lifecycle managed in FastAPI lifespan (main.py).
    """

    def __init__(self):
        self._client: Redis | None = None

    async def connect(self):
        self._client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        await self._client.ping()
        log.info("redis.connected", url=settings.REDIS_URL)

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            log.info("redis.disconnected")

    def _require(self) -> Redis:
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    # ── Core ops ─────────────────────────────────────────────────────────────

    async def ping(self) -> bool:
        return await self._require().ping()

    async def get(self, key: str) -> str | None:
        return await self._require().get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        await self._require().set(key, value, ex=ex)

    async def delete(self, *keys: str):
        if keys:
            await self._require().delete(*keys)

    async def exists(self, key: str) -> bool:
        return bool(await self._require().exists(key))

    async def expire(self, key: str, seconds: int):
        await self._require().expire(key, seconds)

    # ── Set ops (for indexes like user→sessions, user→skills) ────────────────

    async def sadd(self, key: str, *members: str):
        await self._require().sadd(key, *members)

    async def srem(self, key: str, *members: str):
        await self._require().srem(key, *members)

    async def smembers(self, key: str) -> set[str]:
        return await self._require().smembers(key)

    # ── List ops (for message history — ordered insertion) ───────────────────

    async def rpush(self, key: str, *values: str):
        """Append to right of list (newest last)."""
        await self._require().rpush(key, *values)

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        """Get list slice. end=-1 means all."""
        return await self._require().lrange(key, start, end)

    async def llen(self, key: str) -> int:
        return await self._require().llen(key)

    async def ltrim(self, key: str, start: int, end: int):
        """Trim list to range (useful for capping history size)."""
        await self._require().ltrim(key, start, end)

    # ── Pub/Sub (for streaming cancel signals) ────────────────────────────────

    async def publish(self, channel: str, message: str):
        await self._require().publish(channel, message)

    def pubsub(self):
        return self._require().pubsub()

    # ── Increment (for counters) ───────────────────────────────────────────────

    async def incr(self, key: str) -> int:
        return await self._require().incr(key)


# Singleton
redis_client = RedisClient()
# """
# core/redis_client.py — Async Redis Client Wrapper
# ===================================================
# Thin async wrapper around redis.asyncio.
# Provides connect/disconnect lifecycle and typed helpers.
# All session, skill, agent state stored here.
# """

# import redis.asyncio as aioredis
# from redis.asyncio import Redis
# from core.config import settings
# import structlog

# log = structlog.get_logger(__name__)


# class RedisClient:
#     """
#     Async Redis client with explicit connect/disconnect.
#     Lifecycle managed in FastAPI lifespan (main.py).
#     """

#     def __init__(self):
#         self._client: Redis | None = None

#     async def connect(self):
#         self._client = await aioredis.from_url(
#             settings.REDIS_URL,
#             encoding="utf-8",
#             decode_responses=True,
#             max_connections=20,
#         )
#         await self._client.ping()
#         log.info("redis.connected", url=settings.REDIS_URL)

#     async def disconnect(self):
#         if self._client:
#             await self._client.aclose()
#             log.info("redis.disconnected")

#     def _require(self) -> Redis:
#         if not self._client:
#             raise RuntimeError("Redis client not connected. Call connect() first.")
#         return self._client

#     # ── Core ops ─────────────────────────────────────────────────────────────

#     async def ping(self) -> bool:
#         return await self._require().ping()

#     async def get(self, key: str) -> str | None:
#         return await self._require().get(key)

#     async def set(self, key: str, value: str, ex: int | None = None):
#         await self._require().set(key, value, ex=ex)

#     async def delete(self, *keys: str):
#         if keys:
#             await self._require().delete(*keys)

#     async def exists(self, key: str) -> bool:
#         return bool(await self._require().exists(key))

#     async def expire(self, key: str, seconds: int):
#         await self._require().expire(key, seconds)

#     # ── Set ops (for indexes like user→sessions, user→skills) ────────────────

#     async def sadd(self, key: str, *members: str):
#         await self._require().sadd(key, *members)

#     async def srem(self, key: str, *members: str):
#         await self._require().srem(key, *members)

#     async def smembers(self, key: str) -> set[str]:
#         return await self._require().smembers(key)

#     # ── List ops (for message history — ordered insertion) ───────────────────

#     async def rpush(self, key: str, *values: str):
#         """Append to right of list (newest last)."""
#         await self._require().rpush(key, *values)

#     async def lrange(self, key: str, start: int, end: int) -> list[str]:
#         """Get list slice. end=-1 means all."""
#         return await self._require().lrange(key, start, end)

#     async def llen(self, key: str) -> int:
#         return await self._require().llen(key)

#     async def ltrim(self, key: str, start: int, end: int):
#         """Trim list to range (useful for capping history size)."""
#         await self._require().ltrim(key, start, end)

#     # ── Pub/Sub (for streaming cancel signals) ────────────────────────────────

#     async def publish(self, channel: str, message: str):
#         await self._require().publish(channel, message)

#     def pubsub(self):
#         return self._require().pubsub()

#     # ── Increment (for counters) ───────────────────────────────────────────────

#     async def incr(self, key: str) -> int:
#         return await self._require().incr(key)


# # Singleton
# redis_client = RedisClient()
