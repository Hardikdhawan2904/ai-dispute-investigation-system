"""
Database engine and session management for the BFSI Dispute Resolution Platform.
PostgreSQL via psycopg2.
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from dotenv import load_dotenv

from utils.logger import db_logger

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables if they don't exist."""
    import database.models  # noqa: F401 — registers all ORM models
    Base.metadata.create_all(bind=engine)
    db_logger.info("Database initialized — all tables created/verified.")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        db.rollback()
        db_logger.error(f"DB session error: {exc}", exc_info=True)
        raise
    finally:
        db.close()


@contextmanager
def db_session():
    """Context-manager session for use outside FastAPI request scope."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as exc:
        db.rollback()
        db_logger.error(f"DB context error: {exc}", exc_info=True)
        raise
    finally:
        db.close()
