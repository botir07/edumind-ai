"""Cache tests (run with pytest)."""
import asyncio
import pytest

from app.ai_core.cache.service import CacheService
from app.ai_core.cache.providers.memory import MemoryCacheProvider


@pytest.mark.asyncio
async def test_cache_set_get_ttl():
    svc = CacheService(provider=MemoryCacheProvider(), default_ttl=1)
    await svc.set("org1", "ns", "k1", "value1")
    assert await svc.get("org1", "ns", "k1") == "value1"


@pytest.mark.asyncio
async def test_cache_org_isolation():
    svc = CacheService(provider=MemoryCacheProvider())
    await svc.set("org-a", "ns", "k", "secret-a")
    await svc.set("org-b", "ns", "k", "secret-b")
    assert await svc.get("org-a", "ns", "k") == "secret-a"
    assert await svc.get("org-b", "ns", "k") == "secret-b"
    assert await svc.get("org-c", "ns", "k") is None


@pytest.mark.asyncio
async def test_cache_delete_and_clear():
    svc = CacheService(provider=MemoryCacheProvider())
    await svc.set("org1", "ns", "k1", "v1")
    await svc.set("org1", "ns", "k2", "v2")
    assert await svc.get("org1", "ns", "k1") == "v1"
    await svc.delete("org1", "ns", "k1")
    assert await svc.get("org1", "ns", "k1") is None
    assert await svc.get("org1", "ns", "k2") == "v2"
    await svc.clear_namespace("org1", "ns")
    assert await svc.get("org1", "ns", "k2") is None


@pytest.mark.asyncio
async def test_cache_stats():
    svc = CacheService(provider=MemoryCacheProvider())
    await svc.set("org1", "ns", "k1", "v1")
    await svc.get("org1", "ns", "k1")   # hit
    await svc.get("org1", "ns", "missing")  # miss
    st = svc.stats()
    assert st["hits"] >= 1
    assert st["misses"] >= 1
    assert 0.0 <= st["hit_rate"] <= 1.0


@pytest.mark.asyncio
async def test_cache_health():
    svc = CacheService(provider=MemoryCacheProvider())
    assert await svc.health_check() is True
