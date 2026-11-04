"""In-memory cache provider (fallback when Redis unavailable)."""
from typing import Any, Dict, Optional
import time

from app.ai_core.cache.providers.base import CacheProvider


class MemoryCacheProvider(CacheProvider):
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}

    async def get(self, key: str) -> Optional[Any]:
        self._expire(key)
        return self._store.get(key)

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        self._store[key] = value
        if ttl_seconds:
            self._expiry[key] = time.time() + ttl_seconds
        else:
            self._expiry.pop(key, None)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)
        self._expiry.pop(key, None)

    async def clear_namespace(self, namespace: str) -> None:
        prefix = namespace + ":"
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            await self.delete(k)

    async def health_check(self) -> bool:
        return True

    def _expire(self, key: str) -> None:
        exp = self._expiry.get(key)
        if exp and time.time() > exp:
            self._store.pop(key, None)
            self._expiry.pop(key, None)
