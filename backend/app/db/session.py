"""Per-request database session (FastAPI dependency).

Services own transaction boundaries: they call `session.commit()` once a business operation is
complete. Anything not committed is rolled back when the session closes (TECH_STACK.md §24).
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_engine


def get_db() -> Iterator[Session]:
    get_engine()
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
