"""Each route calls the right use case method: the narrow route its own method, the /api/admin
route its admin_ twin. The mock raises, so only 'which method was called' is being checked."""
import pytest

from app.core.errors import ConflictError
from app.modules.issue.factory import get_issue_usecase
from app.modules.measurable.factory import get_measurable_usecase
from app.modules.meeting.factory import get_meeting_usecase
from app.modules.rock.factory import get_rock_usecase
from app.modules.score.factory import get_score_usecase
from app.modules.team.factory import get_team_usecase
from app.modules.todo.factory import get_todo_usecase

W = "2026-11-02"
ROUTES = [
    # (use case factory, http method, path under /api, json body, use case method)
    (get_team_usecase, "GET", "/teams/t1", None, "get_team"),
    (get_team_usecase, "GET", "/teams/t1/members", None, "list_assignable_members"),
    (get_measurable_usecase, "GET", "/teams/t1/measurables", None, "list_for_team"),
    (get_score_usecase, "GET", "/teams/t1/scorecard", None, "get_scorecard"),
    (get_score_usecase, "PUT", f"/measurables/m1/scores/{W}", {"value": 3}, "set_score"),
    (get_rock_usecase, "GET", "/teams/t1/rocks", None, "list_current_rocks"),
    (get_issue_usecase, "GET", "/teams/t1/issues", None, "list_issues"),
    (get_issue_usecase, "POST", "/teams/t1/issues", {"title": "x"}, "create"),
    (get_issue_usecase, "PATCH", "/issues/i1/priority", {"priority": 3}, "set_priority"),
    (get_issue_usecase, "POST", "/issues/i1/solve", {"note": "n"}, "solve"),
    (get_issue_usecase, "POST", f"/measurables/m1/scores/{W}/issue", None, "make_it_an_issue"),
    (get_todo_usecase, "GET", "/teams/t1/todos", None, "list_todos"),
    (get_todo_usecase, "POST", "/issues/i1/todos", {"title": "x", "owner_id": "u2"}, "create_for_issue"),
    (get_todo_usecase, "POST", "/todos/td1/done", None, "mark_done"),
    (get_todo_usecase, "DELETE", "/todos/td1/done", None, "undo_done"),
    (get_meeting_usecase, "POST", "/teams/t1/meetings", None, "start"),
    (get_meeting_usecase, "GET", "/teams/t1/meetings/active", None, "get_active"),
    (get_meeting_usecase, "GET", "/meetings/mt1", None, "get"),
    (get_meeting_usecase, "POST", "/meetings/mt1/join", None, "join"),
    (get_meeting_usecase, "POST", "/meetings/mt1/advance", None, "advance"),
    (get_meeting_usecase, "POST", "/meetings/mt1/end", None, "end"),
    (get_meeting_usecase, "PUT", "/meetings/mt1/rating", {"rating": 5}, "rate"),
]
IDS = [f"{m} {p} -> {name}" for _, m, p, _, name in ROUTES]


@pytest.mark.parametrize("factory,method,path,body,name", ROUTES, ids=IDS)
def test_narrow_route_calls_its_own_method_and_admin_route_calls_the_admin_twin(
    client, mock_usecase, factory, method, path, body, name
):
    uc = mock_usecase(factory)
    for attr in (name, f"admin_{name}"):
        getattr(uc, attr).side_effect = ConflictError("stop here")

    assert client.request(method, f"/api{path}", json=body).status_code == 409
    getattr(uc, name).assert_called_once()
    getattr(uc, f"admin_{name}").assert_not_called()

    uc.reset_mock()
    assert client.request(method, f"/api/admin{path}", json=body).status_code == 409
    getattr(uc, f"admin_{name}").assert_called_once()
    getattr(uc, name).assert_not_called()


def test_every_team_scoped_route_has_an_admin_twin(app):
    paths = set(app.openapi()["paths"])
    admin = {p for p in paths if p.startswith("/api/admin/")}
    assert len(admin) >= 17
    for p in admin:
        assert p.replace("/api/admin", "/api", 1) in paths, f"{p} has no narrow counterpart"
