"""Abstract cache provider interface."""
from typing import Any, Optional


class CacheProvider:
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError

    async def clear_namespace(self, namespace: str) -> None:
        raise NotImplementedError

    async def health_check(self) -> bool:
        raise NotImplementedError
