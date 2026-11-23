"""Repository tests run against a real Postgres: partial unique indexes, ON CONFLICT and CHECK
constraints only exist there. The schema comes from the real Alembic migrations, so the migrations
are tested too. Each test runs in a transaction that is rolled back; nothing leaks between tests.
"""
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.modules.team.models import Membership, Team
from app.modules.user.models import User

SERVER_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def db_engine():
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


@pytest.fixture
def session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    # SAVEPOINT mode: code under test may commit/rollback/begin_nested; the outer transaction still rolls back.
    s = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    yield s
    s.close()
    transaction.rollback()
    connection.close()


def add(session, *entities):
    """Persist entities one at a time so foreign-key order is always respected."""
    for e in entities:
        session.add(e)
        session.flush()
    return entities[0] if len(entities) == 1 else entities


@pytest.fixture
def world(session):
    """Two teams and four users: u1 admin (t1), u2 + u3 team members, u4 observer (t1)."""
    add(session, Team(id="t1", name="Leadership"), Team(id="t2", name="Ops"))
    add(session,
        User(id="u1", name="Avery", email="avery@acme.test", role="admin"),
        User(id="u2", name="Blake", email="blake@acme.test", role="team_member"),
        User(id="u3", name="Casey", email="casey@acme.test", role="team_member"),
        User(id="u4", name="Dana", email="dana@acme.test", role="observer"))
    add(session, Membership(user_id="u1", team_id="t1"), Membership(user_id="u2", team_id="t1"),
        Membership(user_id="u4", team_id="t1"), Membership(user_id="u2", team_id="t2"),
        Membership(user_id="u3", team_id="t2"))
    return session


@pytest.fixture(scope="session")
def alembic_cfg(db_engine):
    cfg = Config()
    cfg.set_main_option("script_location", str(SERVER_DIR / "alembic"))
    return cfg


def violates(session, *entities):
    """Assert the database itself rejects these rows (the savepoint keeps the session usable)."""
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            for e in entities:
                session.add(e)
                session.flush()
