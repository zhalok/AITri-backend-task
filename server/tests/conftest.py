"""Test configuration.

Clock strategy: nothing reads the system clock for business time. Production code takes "now" from
APP_NOW; here it is pinned to the seed's "now" (2026-11-11T15:00:00Z, Wednesday 9:00 AM Chicago),
and service tests build a Clock at any instant they need. Auth tokens use the real clock on purpose.

Database strategy: tests never touch the dev database. DATABASE_URL is forced to a separate
`l10_test` database on the same Postgres (override with TEST_DATABASE_URL). Repository tests build
its schema from the real Alembic migrations, then run each test in a transaction that is rolled back.
"""
import os

# Must run before anything imports app.* (settings and the engine are created at import time).
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/l10_test"
)
os.environ["APP_NOW"] = "2026-11-11T15:00:00Z"
os.environ["COMPANY_TIMEZONE"] = "America/Chicago"
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-32b"
os.environ["JWT_EXPIRE_MINUTES"] = "480"

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402

from tests.helpers import make_clock  # noqa: E402

SERVER_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def clock():
    """Fixed clock at the seed's 'now'."""
    return make_clock()


@pytest.fixture(scope="session")
def db_engine():
    """A real Postgres with the real migrations applied, shared by the repository and the real-database API tests."""
    url = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(text("select 1 from pg_database where datname = :n"), {"n": url.database}).scalar()
            if not exists:
                conn.execute(text(f'create database "{url.database}"'))
    except OperationalError as exc:
        pytest.fail(
            f"Postgres is not reachable at {url.host}:{url.port}. Start it with: docker compose up -d --wait db\n{exc}",
            pytrace=False,
        )
    finally:
        admin.dispose()

    engine = create_engine(url)
    with engine.begin() as conn:  # fresh schema every run, then the real migrations
        conn.execute(text("drop schema public cascade"))
        conn.execute(text("create schema public"))
    cfg = Config()
    cfg.set_main_option("script_location", str(SERVER_DIR / "alembic"))
    command.upgrade(cfg, "head")  # alembic/env.py reads DATABASE_URL, which conftest points at the test DB
    yield engine
    engine.dispose()
