"""Test fixtures.

Unit and API tests run without Oracle or Redis:
- the database is an in-memory SQLite created from the SQLAlchemy models (fast, isolated);
- Redis is replaced by tests/fakes.py.
Oracle-specific behaviour is covered by running the app against the Docker stack
(see README "Verify the stack"); mark such tests with @pytest.mark.integration.
"""

from __future__ import annotations

import base64
import os
from collections.abc import Iterator

import pytest

# Settings must exist before the app is imported.
os.environ.update(
    {
        "APP_ENV": "test",
        "JWT_SECRET": base64.b64encode(os.urandom(64)).decode(),
        "AES_ENCRYPTION_KEY": base64.b64encode(os.urandom(32)).decode(),
        "BLIND_INDEX_KEY": base64.b64encode(os.urandom(32)).decode(),
        "COOKIE_SECURE": "false",
        "PUBLIC_ORIGIN": "http://testserver",
        "CORS_ORIGINS": "",
        "LOG_LEVEL": "WARNING",
        "LOGIN_MAX_FAILURES": "3",
        "STORAGE_BACKEND": "local",
    }
)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.cache.redis import get_redis
from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.session import get_db
from app.main import create_app
from app.models import AppModule, AppUser, AuditChain, Base, UserModuleRole
from app.models.audit import GENESIS_HASH
from tests.fakes import FakeRedis

PASSWORD = "Correct-Horse-Battery-9"
WEB_HEADERS = {"X-DMS-Client": "web"}


@pytest.fixture
def settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def engine():  # type: ignore[no-untyped-def]
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_conn, _):  # type: ignore[no-untyped-def]
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine) -> sessionmaker[Session]:  # type: ignore[no-untyped-def]
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session


@pytest.fixture
def redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def seeded(db: Session) -> dict[str, AppUser]:
    db.add(AuditChain(id=1, last_hash=GENESIS_HASH))
    db.add_all(
        [
            AppModule(code="UPI", name="UPI", description="UPI disputes", is_enabled=True, display_order=1),
            AppModule(code="IMPS", name="IMPS", description="IMPS disputes", is_enabled=False, display_order=2),
        ]
    )
    maker = AppUser(
        username="dev_user",
        display_name="Developer",
        auth_source="LOCAL",
        status="ACTIVE",
        password_hash=hash_password(PASSWORD),
    )
    no_roles = AppUser(
        username="no_roles",
        display_name="No Roles",
        auth_source="LOCAL",
        status="ACTIVE",
        password_hash=hash_password(PASSWORD),
    )
    disabled = AppUser(
        username="disabled_user",
        display_name="Disabled",
        auth_source="LOCAL",
        status="DISABLED",
        password_hash=hash_password(PASSWORD),
    )
    db.add_all([maker, no_roles, disabled])
    db.flush()
    db.add_all(
        [
            UserModuleRole(user_id=maker.id, module_code="UPI", role_code="MAKER"),
            UserModuleRole(user_id=maker.id, module_code="UPI", role_code="ADMIN"),
        ]
    )
    db.commit()
    return {"maker": maker, "no_roles": no_roles, "disabled": disabled}


@pytest.fixture
def client(
    settings: Settings, session_factory: sessionmaker[Session], redis: FakeRedis, seeded: dict[str, AppUser]
) -> Iterator[TestClient]:
    app = create_app(settings)

    def _db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_redis] = lambda: redis
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str = "dev_user", password: str = PASSWORD):  # type: ignore[no-untyped-def]
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
