from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_session
from app.core.errors import (ConflictError, DomainValidationError, ForbiddenError, NotFoundError,
                             UnauthorizedError)
from app.main import create_app
from app.modules.auth.factory import get_auth_service
from app.modules.team.factory import get_team_usecase
from tests.helpers import make_team, make_user


# ---- AppError -> HTTP ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "error,status,code",
    [
        (UnauthorizedError("no"), 401, "unauthorized"),
        (ForbiddenError("no"), 403, "forbidden"),
        (NotFoundError("gone"), 404, "not_found"),
        (ConflictError("dup"), 409, "conflict"),
        (DomainValidationError("bad"), 422, "validation_error"),
    ],
)
def test_domain_errors_become_json_with_a_stable_shape(client, mock_usecase, error, status, code):
    mock_usecase(get_team_usecase).get_team.side_effect = error
    r = client.get("/api/teams/t1")
    assert r.status_code == status
    assert r.json() == {"error": code, "message": str(error)}


def test_the_success_path_for_the_same_route(client, mock_usecase):
    mock_usecase(get_team_usecase).get_team.return_value = make_team("t1", "Leadership")
    r = client.get("/api/teams/t1")
    assert r.status_code == 200 and r.json() == {"id": "t1", "name": "Leadership"}


# ---- the authentication gate ----------------------------------------------------------------------

class FakeAuth:
    def user_from_token(self, token):
        if token == "good":
            return make_user("u_real")
        raise UnauthorizedError("Invalid or expired token")


@pytest.fixture
def anon():
    """A client with the real get_current_user: no override of the gate itself."""
    app = create_app()
    app.dependency_overrides[get_session] = lambda: None
    app.dependency_overrides[get_auth_service] = lambda: FakeAuth()
    return app, TestClient(app)


def fill(path):
    return path.replace("{week_start}", "2026-11-02").replace("{", "").replace("}", "")


def all_protected_operations(app):
    for path, ops in app.openapi()["paths"].items():
        if path == "/api/auth/login":
            continue
        for method in ops:
            yield method.upper(), fill(path)


def test_there_is_a_meaningful_number_of_protected_routes(anon):
    app, _ = anon
    assert len(list(all_protected_operations(app))) >= 45


def test_every_route_except_login_refuses_a_request_without_a_token(anon):
    app, client = anon
    leaks = [(m, p) for m, p in all_protected_operations(app) if client.request(m, p).status_code != 401]
    assert leaks == []


@pytest.mark.parametrize("header", ["Bearer bad", "Bearer ", "Basic good", "good", "bearer"])
def test_bad_credentials_are_refused_on_every_route(anon, header):
    app, client = anon
    leaks = [(m, p) for m, p in all_protected_operations(app)
             if client.request(m, p, headers={"Authorization": header}).status_code != 401]
    assert leaks == []


def test_a_valid_token_gets_through_to_the_use_case(anon):
    app, client = anon
    uc = MagicMock()
    uc.list_my_teams.return_value = [make_team("t1", "Leadership")]
    from app.modules.team.factory import get_team_usecase as factory
    app.dependency_overrides[factory] = lambda: uc
    r = client.get("/api/teams", headers={"Authorization": "Bearer good"})
    assert r.status_code == 200
    assert uc.list_my_teams.call_args.args[0].id == "u_real"  # the token's user is the actor


def test_login_is_public(anon):
    _, client = anon
    assert client.post("/api/auth/login", json={}).status_code == 422  # reaches validation, not a 401


def test_auth_error_body_shape(anon):
    _, client = anon
    r = client.get("/api/teams")
    assert r.status_code == 401 and r.json() == {"error": "unauthorized", "message": "Authentication required"}
