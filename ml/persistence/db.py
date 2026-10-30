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

# Default to a local SQLite DB when no env var is set (used for development).
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./postureai.db"
)
# If a postgres URL is provided without async driver, adapt it for SQLAlchemy async.
if DATABASE_URL.startswith("postgresql://"):
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    parsed = urlparse(DATABASE_URL)
    query = dict(parse_qsl(parsed.query))
    if "sslmode" not in query:
        query["sslmode"] = "require"
    new_query = urlencode(query)
    DATABASE_URL = urlunparse((
        "postgresql+psycopg",
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))

# Async engine – ``future=True`` enables 2.0 style usage.
engine = create_async_engine(DATABASE_URL, future=True, echo=False)

# Session factory – ``expire_on_commit=False`` prevents lazy loading after
# the session is closed, which is convenient for our simple use‑case.
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for model declarations.
Base = declarative_base()
