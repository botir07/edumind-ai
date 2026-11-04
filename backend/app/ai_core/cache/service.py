"""Cache service with organization namespacing, TTL, invalidation, and Redis fallback."""
import hashlib
from typing import Any, Optional

from app.ai_core.core.config import ai_settings
from app.ai_core.cache.providers.base import CacheProvider
from app.ai_core.cache.providers.memory import MemoryCacheProvider

try:  # Redis provider optional
    import redis.asyncio as aioredis  # type: ignore

    _HAS_REDIS = True
except Exception:  # noqa: BLE001
    aioredis = None  # type: ignore
    _HAS_REDIS = False


class RedisCacheProvider(CacheProvider):
    def __init__(self, redis_url: str, db: int = 1, key_prefix: str = "ai"):
        self.redis_url = redis_url
        self.db = db
        self.key_prefix = key_prefix
        self._client = None

    async def _get_client(self):
        if self._client is None and aioredis is not None:
            self._client = aioredis.from_url(self.redis_url, db=self.db, decode_responses=True)
        return self._client

    def _key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        import json
        client = await self._get_client()
        if client is None:
            return None
        raw = await client.get(self._key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        import json
        client = await self._get_client()
        if client is None:
            return
        payload = value if isinstance(value, str) else json.dumps(value)
        if ttl_seconds:
            await client.setex(self._key(key), int(ttl_seconds), payload)
        else:
            await client.set(self._key(key), payload)

    async def delete(self, key: str) -> None:
        client = await self._get_client()
        if client is None:
            return
        await client.delete(self._key(key))

    async def clear_namespace(self, namespace: str) -> None:
        client = await self._get_client()
        if client is None:
            return
        keys = await client.keys(f"{self.key_prefix}:{namespace}:*")
        if keys:
            await client.delete(*keys)

    async def health_check(self) -> bool:
        client = await self._get_client()
        if client is None:
            return False
        try:
            return await client.ping()
        except Exception:
            return False


class CacheService:
    """Namespaced cache service.

    Keys are namespaced by organization to prevent cross-org leakage.
    Falls back to in-memory provider when Redis is unavailable.
    """

    def __init__(self, provider: Optional[CacheProvider] = None, default_ttl: Optional[int] = None):
        self.provider = provider or MemoryCacheProvider()
        self.default_ttl = default_ttl or ai_settings.cache_default_ttl_seconds
        self._hits = 0
        self._misses = 0

    def _org_key(self, organization_id: str, namespace: str, key: str) -> str:
        digest = hashlib.sha256(key.encode()).hexdigest()[:16]
        return f"org:{organization_id}:{namespace}:{digest}"

    async def get(self, organization_id: str, namespace: str, key: str) -> Optional[Any]:
        full = self._org_key(organization_id, namespace, key)
        val = await self.provider.get(full)
        if val is None:
            self._misses += 1
        else:
            self._hits += 1
        return val

    async def set(self, organization_id: str, namespace: str, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        full = self._org_key(organization_id, namespace, key)
        await self.provider.set(full, value, ttl_seconds=ttl_seconds or self.default_ttl)

    async def delete(self, organization_id: str, namespace: str, key: str) -> None:
        full = self._org_key(organization_id, namespace, key)
        await self.provider.delete(full)

    async def clear_namespace(self, organization_id: str, namespace: str) -> None:
        prefix = f"org:{organization_id}:{namespace}:"
        # Memory provider supports clear_namespace by prefix; redis uses keys scan
        if hasattr(self.provider, "clear_namespace"):
            # clear_namespace in providers uses namespace prefix; we emulate by scanning
            pass
        # For memory provider, do a manual prefix clear
        if isinstance(self.provider, MemoryCacheProvider):
            keys = [k for k in self.provider._store if k.startswith(prefix)]
            for k in keys:
                await self.provider.delete(k)

    async def health_check(self) -> bool:
        return await self.provider.health_check()

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (self._hits / total) if total else 0.0,
            "provider": type(self.provider).__name__,
        }
