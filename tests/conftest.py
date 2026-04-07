import pytest

from httpx import AsyncClient, ASGITransport

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.models import asset as asset_models
from app.models import job_run as job_run_models
from app.models import mode as mode_models
from app.models import patch as patch_models
from app.core.config import settings

TEST_DATABASE_URL = "sqlite://"

settings.ENABLE_PATCH_POLLER = False

# Import model modules so all tables are registered on Base.metadata for tests.
assert asset_models and job_run_models and mode_models and patch_models


class AsyncSessionAdapter:
    def __init__(self, session: Session):
        self._session = session

    def add(self, instance):
        self._session.add(instance)

    def add_all(self, instances):
        self._session.add_all(instances)

    async def commit(self):
        self._session.commit()

    async def rollback(self):
        self._session.rollback()

    async def execute(self, statement, *args, **kwargs):
        return self._session.execute(statement, *args, **kwargs)

    async def close(self):
        self._session.close()


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
async def db_connection(engine):
    connection = engine.connect()
    transaction = connection.begin()

    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()

@pytest.fixture
async def db_session(db_connection):
    session_factory = sessionmaker(
        bind=db_connection,
        expire_on_commit=False,
    )

    session = session_factory()

    try:
        yield AsyncSessionAdapter(session)
    finally:
        session.close()


@pytest.fixture
async def client(db_connection):
    session_factory = sessionmaker(
        bind=db_connection,
        expire_on_commit=False,
    )

    async def override_get_db():
        session = session_factory()
        try:
            yield AsyncSessionAdapter(session)
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
