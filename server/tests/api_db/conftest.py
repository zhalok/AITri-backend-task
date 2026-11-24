"""API tests against a REAL database: HTTP in, the real app and use cases in the middle, real SQL at the bottom.

Where the answer depends on a query (which teams a user belongs to, whose members are listed, unique indexes, row
locks) a fake repository would only test the fake, so these tests use the real Postgres schema (built from the
migrations) loaded with the real seed.json. Each test runs inside one transaction that is rolled back afterwards,
so the seed and anything a test writes never persist and the tests cannot disturb each other.
"""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.main import create_app
from app.seed import DEFAULT_SEED, load_seed
from tests.api.conftest import Api

SEED = json.loads(DEFAULT_SEED.read_text())


@pytest.fixture(scope="module")
def seeded_connection(db_engine):
    """One connection holding one outer transaction with the seed loaded once; nothing here is ever committed."""
    connection = db_engine.connect()
    outer = connection.begin()
    with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as s:
        load_seed(s, SEED)
        s.commit()
    yield connection
    outer.rollback()
    connection.close()


@pytest.fixture
def live(seeded_connection):
    """A client for one test. Whatever the test writes is undone when it ends (it ran inside a SAVEPOINT)."""
    savepoint = seeded_connection.begin_nested()
    # Requests commit for real as far as the app can tell, but only to nested savepoints.
    session = Session(bind=seeded_connection, join_transaction_mode="create_savepoint", expire_on_commit=False)

    app = create_app()

    def request_session():
        yield session  # one connection, so requests are handled one at a time

    app.dependency_overrides[get_session] = request_session
    yield Api(TestClient(app))
    session.close()
    savepoint.rollback()
