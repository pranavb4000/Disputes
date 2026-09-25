"""SQLAlchemy engine for Oracle via python-oracledb (thin mode: no Oracle Instant Client needed)."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings, get_settings


def build_oracle_url(settings: Settings) -> URL:
    return URL.create(
        "oracle+oracledb",
        username=settings.database_user,
        password=settings.database_password.get_secret_value(),
        host=settings.database_host,
        port=settings.database_port,
        query={"service_name": settings.database_service},
    )


def create_db_engine(settings: Settings) -> Engine:
    return create_engine(
        build_oracle_url(settings),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=settings.db_echo,
    )


_engine: Engine | None = None
SessionLocal = sessionmaker(autoflush=False, expire_on_commit=False)


def get_engine() -> Engine:
    """Create the engine lazily so importing the app never opens a DB connection."""
    global _engine
    if _engine is None:
        _engine = create_db_engine(get_settings())
        SessionLocal.configure(bind=_engine)
    return _engine
