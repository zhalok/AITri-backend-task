from datetime import date

import pytest

from app.modules.meeting.factory import get_meeting_usecase
from app.modules.meeting.service import MeetingState
from app.modules.todo.factory import get_todo_usecase
from app.modules.todo.service import TodoView
from tests.helpers import NOW, make_todo


# ---- To-Dos -------------------------------------------------------------------------------------

@pytest.fixture
def todos(mock_usecase):
    return mock_usecase(get_todo_usecase)


def test_todo_list_shape_includes_the_computed_overdue_flag(client, todos, actor):
    todos.list_todos.return_value = [
        TodoView(make_todo("a", due_date=date(2026, 11, 1)), True),
        TodoView(make_todo("b", due_date=date(2026, 11, 20), source_issue_id="i1"), False),
    ]
    r = client.get("/api/teams/t1/todos")
    assert r.status_code == 200
    a, b = r.json()
    assert (a["id"], a["is_overdue"], a["due_date"], a["done_at"]) == ("a", True, "2026-11-01", None)
    assert (b["is_overdue"], b["source_issue_id"]) == (False, "i1")
    assert set(a) >= {"id", "team_id", "owner_id", "title", "due_date", "done_at", "created_at",
                      "source_issue_id", "created_in_meeting_id", "is_overdue"}
    todos.list_todos.assert_called_once_with(actor, "t1")


def test_create_todo_for_an_issue(client, todos, actor):
    todos.create_for_issue.return_value = TodoView(make_todo("n", source_issue_id="i1"), False)
    r = client.post("/api/issues/i1/todos", json={"title": "  Call vendor ", "owner_id": "u3"})
    assert r.status_code == 201 and r.json()["source_issue_id"] == "i1"
    todos.create_for_issue.assert_called_once_with(actor, "i1", "Call vendor", "u3")


@pytest.mark.parametrize(
    "body",
    [{}, {"title": "x"}, {"owner_id": "u3"}, {"title": "", "owner_id": "u3"}, {"title": "  ", "owner_id": "u3"},
     {"title": "x" * 301, "owner_id": "u3"}, {"title": "x", "owner_id": None}],
)
def test_create_todo_rejects_invalid_input(client, todos, body):
    assert client.post("/api/issues/i1/todos", json=body).status_code == 422
    todos.create_for_issue.assert_not_called()


def test_mark_done_and_undo(client, todos, actor):
    todos.mark_done.return_value = TodoView(make_todo(done_at=NOW), False)
    todos.undo_done.return_value = TodoView(make_todo(), False)
    assert client.post("/api/todos/td1/done").json()["done_at"] == "2026-11-11T15:00:00Z"
    assert client.delete("/api/todos/td1/done").json()["done_at"] is None
    todos.mark_done.assert_called_once_with(actor, "td1")
    todos.undo_done.assert_called_once_with(actor, "td1")


# ---- Meetings -----------------------------------------------------------------------------------

@pytest.fixture
def meetings(mock_usecase):
    return mock_usecase(get_meeting_usecase)


def state(**kw):
    base = dict(id="mt1", team_id="t1", facilitator_id="u2", started_at=NOW, ended_at=None,
                current_section="scorecard", section_started_at=NOW, section_duration_seconds=300,
                section_elapsed_seconds=42, over_time=False, attendee_ids=["u2", "u3"], ratings={}, average_rating=None)
    return MeetingState(**{**base, **kw})


def test_start_returns_201_and_the_full_state(client, meetings, actor):
    meetings.start.return_value = state()
    r = client.post("/api/teams/t1/meetings")
    assert r.status_code == 201
    assert r.json() == {
        "id": "mt1", "team_id": "t1", "facilitator_id": "u2", "started_at": "2026-11-11T15:00:00Z",
        "ended_at": None, "current_section": "scorecard", "section_started_at": "2026-11-11T15:00:00Z",
        "section_duration_seconds": 300, "section_elapsed_seconds": 42, "over_time": False,
        "attendee_ids": ["u2", "u3"], "ratings": {}, "average_rating": None,
    }
    meetings.start.assert_called_once_with(actor, "t1")


def test_active_meeting_is_null_when_there_is_none(client, meetings):
    meetings.get_active.return_value = None
    r = client.get("/api/teams/t1/meetings/active")
    assert r.status_code == 200 and r.json() is None


def test_over_time_and_average_are_passed_through(client, meetings):
    meetings.get.return_value = state(current_section="conclude", over_time=True, ratings={"u2": 8, "u3": 9},
                                      average_rating=8.5)
    body = client.get("/api/meetings/mt1").json()
    assert body["over_time"] is True and body["average_rating"] == 8.5 and body["ratings"] == {"u2": 8, "u3": 9}


@pytest.mark.parametrize("verb,path,method", [
    ("post", "/api/meetings/mt1/join", "join"),
    ("post", "/api/meetings/mt1/advance", "advance"),
    ("post", "/api/meetings/mt1/end", "end"),
])
def test_meeting_commands_return_the_new_state(client, meetings, actor, verb, path, method):
    getattr(meetings, method).return_value = state(current_section="ids")
    r = getattr(client, verb)(path)
    assert r.status_code == 200 and r.json()["current_section"] == "ids"
    getattr(meetings, method).assert_called_once_with(actor, "mt1")


@pytest.mark.parametrize("rating", [1, 5, 10])
def test_rating_boundaries_are_accepted(client, meetings, actor, rating):
    meetings.rate.return_value = state(ratings={"u_actor": rating})
    assert client.put("/api/meetings/mt1/rating", json={"rating": rating}).status_code == 200
    meetings.rate.assert_called_once_with(actor, "mt1", rating)


@pytest.mark.parametrize("body", [{}, {"rating": 0}, {"rating": 11}, {"rating": -3}, {"rating": 7.5},
                                  {"rating": "nine"}, {"rating": None}])
def test_rating_rejects_values_outside_1_to_10(client, meetings, body):
    r = client.put("/api/meetings/mt1/rating", json=body)
    assert r.status_code == 422
    meetings.rate.assert_not_called()
