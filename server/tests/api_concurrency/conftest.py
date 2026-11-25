"""Concurrency API tests need REAL, COMMITTED transactions: a race only exists between separate connections.

So this suite does not use the shared rolled-back test database. It builds a throwaway database of its own
(`l10_concurrency`, migrations + seed, committed), points the app's sessions at it, and drops it afterwards.
"""
import json
import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.database import get_session
from app.main import create_app
from app.seed import DEFAULT_SEED, load_seed
from tests.api.conftest import Api
from tests.conftest import SERVER_DIR

DB_NAME = "l10_concurrency"


@pytest.fixture(scope="module")
def race_engine():
    base = make_url(os.environ["DATABASE_URL"])
    url = base.set(database=DB_NAME)
    admin = create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'drop database if exists "{DB_NAME}" with (force)'))
        conn.execute(text(f'create database "{DB_NAME}"'))

    # alembic reads the URL from settings; point it at the new database just for the migration
    previous = os.environ["DATABASE_URL"]
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
    get_settings.cache_clear()
    try:
        cfg = Config()
        cfg.set_main_option("script_location", str(SERVER_DIR / "alembic"))
        command.upgrade(cfg, "head")
    finally:
        os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()

    engine = create_engine(url, pool_size=10)
    with Session(engine) as s:
        load_seed(s, json.loads(DEFAULT_SEED.read_text()))
        s.commit()
    yield engine
    engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'drop database if exists "{DB_NAME}" with (force)'))
    admin.dispose()


@pytest.fixture
def race_api(race_engine):
    """The real app; every request gets its own session and its own transaction, committed for real."""
    maker = sessionmaker(bind=race_engine, expire_on_commit=False)

    def request_session():
        session = maker()  # same shape as app.core.database.get_session, on the throwaway database
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_session] = request_session
    with TestClient(app) as client:
        yield Api(client), race_engine
