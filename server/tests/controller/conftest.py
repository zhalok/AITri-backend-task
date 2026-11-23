"""Controller tests exercise HTTP only: routing, validation, status codes, response shapes.

Every use case is replaced by a MagicMock, the DB session by None, and the authenticated user by a
fixed actor. Nothing below the controller runs.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_session
from app.main import create_app
from tests.helpers import make_user


@pytest.fixture
def actor():
    return make_user("u_actor", "team_member")


@pytest.fixture
def app(actor):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: actor
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_usecase(app):
    """mock_usecase(get_issue_usecase) -> a MagicMock standing in for that use case."""

    def install(factory):
        mock = MagicMock()
        app.dependency_overrides[factory] = lambda: mock
        return mock

    return install
