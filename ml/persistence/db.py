# ml/persistence/db.py
"""Database engine and session management for the persistence layer.

Uses SQLAlchemy async engine. The connection URL is taken from the
environment variable ``DATABASE_URL``. If the variable is not defined a
fallback SQLite in‑memory database is used – this is helpful for the unit
tests.
"""

import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Default to an in‑memory SQLite DB when no env var is set (used by tests).
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./test.db"
)

# Async engine – ``future=True`` enables 2.0 style usage.
engine = create_async_engine(DATABASE_URL, future=True, echo=False)

# Session factory – ``expire_on_commit=False`` prevents lazy loading after
# the session is closed, which is convenient for our simple use‑case.
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for model declarations.
Base = declarative_base()
