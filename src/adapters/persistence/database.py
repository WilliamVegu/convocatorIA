"""Database engine and session management for ATS Core MVP."""
from __future__ import annotations

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import config
from src.adapters.persistence.models import Base
from src.adapters.persistence.ddl import install_immutability_triggers


def create_app_engine(db_url: str | None = None) -> Engine:
    """Create configured SQLAlchemy 2.0 engine with SQLite pragmas."""
    url = db_url or config.DATABASE_URL
    is_sqlite = url.startswith("sqlite")

    connect_args = {}
    if is_sqlite:
        connect_args["check_same_thread"] = False

    engine = create_engine(url, connect_args=connect_args)

    if is_sqlite:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("PRAGMA busy_timeout = 5000;")
            if not url.endswith(":memory:"):
                try:
                    cursor.execute("PRAGMA journal_mode = WAL;")
                except Exception:
                    pass
            cursor.close()

    return engine


engine = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine: Engine | None = None) -> None:
    """Initialize database tables and immutability triggers."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)
    if str(eng.url).startswith("sqlite"):
        install_immutability_triggers(eng)


def get_db() -> Generator[Session, None, None]:
    """Yield database session context."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
