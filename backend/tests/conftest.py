"""Test fixtures. API tests run against a dedicated `pytest` schema in the local database,
migrated with Alembic at session start and truncated before each test (TS-001)."""

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.api.ratelimit import limiter
from app.config import settings
from app.db.session import get_session
from app.main import app

TEST_SCHEMA = "pytest"
TEST_URL = f"{settings.database_url}?options=-csearch_path%3D{TEST_SCHEMA}"
TABLES = "feedback, share_link, report, assessment"


@pytest.fixture(scope="session")
def engine():
    admin = create_engine(settings.database_url)
    with admin.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_URL.replace("%", "%%"))
    command.upgrade(cfg, "head")
    eng = create_engine(TEST_URL)
    yield eng
    eng.dispose()
    with admin.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
    admin.dispose()


@pytest.fixture
def db(engine) -> Iterator[Session]:
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session


@pytest.fixture
def client(db) -> Iterator[TestClient]:
    def _session() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_session] = _session
    limiter.enabled = False
    with TestClient(app) as c:
        yield c
    limiter.enabled = True
    limiter.reset()
    app.dependency_overrides.clear()
