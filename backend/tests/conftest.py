"""Pytest configuration and fixtures for backend tests.

Tests run against a local SQLite database (aiosqlite) so the suite is runnable
without a provisioned PostgreSQL server. Production/development use PostgreSQL
via DATABASE_URL. Schema is created from SQLAlchemy metadata (same model
definitions that Alembic migrates to PostgreSQL).
"""
import asyncio
import os
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Force SQLite for tests before the app imports its engine.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-do-not-use-in-production")

from app.main import app as fastapi_app  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import get_db, engine, AsyncSessionLocal  # noqa: E402
import app.models  # noqa: E402  (register models on Base.metadata)

TEST_ENGINE = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TEST_SESSION_MAKER = async_sessionmaker(
    TEST_ENGINE, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await TEST_ENGINE.dispose()


@pytest.fixture
async def db() -> AsyncSession:
    async with TEST_SESSION_MAKER() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()
