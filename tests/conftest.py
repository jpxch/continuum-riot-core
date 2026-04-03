import asyncio
import pytest

from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event

from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.core.config import settings

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

settings.ENABLE_PATCH_POLLER = False


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    pytest.importorskip(
        "aiosqlite",
        reason="Test DB driver missing. Install dev deps (e.g. `pip install -e '.[dev]'`).",
    )
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_connection(engine):
    async with engine.connect() as conn:
        trans = await conn.begin()

        try:
            yield conn
        finally:
            await trans.rollback()

@pytest.fixture
async def db_session(db_connection):
    async_session = async_sessionmaker(
        bind=db_connection,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_connection):
    async_session = async_sessionmaker(
        bind=db_connection,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
