import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

log = logging.getLogger(__name__)


class Cache:
    def __init__(self, url: str):
        self._url = url
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        self._client = redis.from_url(self._url, decode_responses=True)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def get_json(self, key: str) -> Any | None:
        if self._client is None:
            return None
        try:
            raw = await self._client.get(key)
        except redis.RedisError as e:
            log.warning("cache get failed for %s: %s", key, e)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set_json(self, key: str, value: Any, ttl: int) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(key, json.dumps(value, default=str), ex=ttl)
        except redis.RedisError as e:
            log.warning("cache set failed for %s: %s", key, e)

    async def get_stale(self, key: str) -> Any | None:
        """Return a stale (no-TTL) fallback copy kept under key+':stale'."""
        return await self.get_json(f"{key}:stale")

    async def set_stale(self, key: str, value: Any) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(f"{key}:stale", json.dumps(value, default=str))
        except redis.RedisError as e:
            log.warning("stale cache set failed for %s: %s", key, e)


cache = Cache(settings.redis_url)
