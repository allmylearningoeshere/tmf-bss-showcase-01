"""
Database engine and session management.

The connection string comes from the DATABASE_URL environment variable, which
is set in the Render dashboard (never committed). If it is absent — e.g. a
local run without a database — the app falls back to a local SQLite file so
development still works without provisioning Postgres.

Neon note: the pooled connection string is preferred for a web backend, and
`sslmode=require` is mandatory. Neon's compute suspends when idle and resumes
on the next query, so `pool_pre_ping` is enabled to transparently discard
connections that were dropped during a suspend.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ---------------------------------------------------------------------------
# Connection string
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# SQLAlchemy expects the "postgresql://" scheme. Some providers hand out
# "postgres://", so normalise it.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fallback for local development without a database configured.
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./local_dev.db"

IS_SQLITE = DATABASE_URL.startswith("sqlite")


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

engine_kwargs: dict = {
    # Verify a connection is alive before handing it out. Essential with Neon,
    # whose compute suspends after idle and closes pooled connections.
    "pool_pre_ping": True,
    "future": True,
}

if IS_SQLITE:
    # SQLite needs this to be usable across FastAPI's threadpool.
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Keep the pool small — Neon's free tier has a modest connection ceiling
    # and a web backend does not need many concurrent connections.
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 5
    # Recycle connections well before any server-side idle timeout.
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db():
    """
    Yields a database session for the lifetime of one request, then closes it.

    Usage in a route:
        def handler(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_initialised = False


def init_db(force: bool = False) -> None:
    """
    Creates any missing tables.

    Alembic owns schema migrations, but calling this makes a fresh database
    (or a fresh local SQLite file) usable immediately without a separate
    migration step. It is a no-op when the tables already exist.

    Runs at most once per process unless `force=True`.
    """
    global _initialised
    if _initialised and not force:
        return

    from shared.db import models  # noqa: F401  (registers models on Base)

    Base.metadata.create_all(bind=engine)
    _initialised = True


def ensure_initialised() -> None:
    """
    Guarantees the schema exists before the first query.

    The startup hook normally handles this, but a session can be requested
    before (or without) startup running — under TestClient, or if the hook
    fails. Rather than let that surface as "no such table" on every request,
    the first session use initialises the schema itself.
    """
    if not _initialised:
        init_db()
