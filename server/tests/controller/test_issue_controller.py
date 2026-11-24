import pytest

from app.modules.issue.factory import get_issue_usecase
from tests.helpers import NOW, make_issue

W = "2026-11-02"


@pytest.fixture
def uc(mock_usecase):
    return mock_usecase(get_issue_usecase)


def test_list_defaults_to_unsolved(client, uc, actor):
    uc.list_issues.return_value = [make_issue("i1", priority=5), make_issue("i2")]
    r = client.get("/api/teams/t1/issues")
    assert r.status_code == 200
    assert [i["id"] for i in r.json()] == ["i1", "i2"]  # order is the use case's; the controller keeps it
    uc.list_issues.assert_called_once_with(actor, "t1", solved=False)


def test_list_solved(client, uc, actor):
    uc.list_issues.return_value = []
    assert client.get("/api/teams/t1/issues?status=solved").json() == []
    uc.list_issues.assert_called_once_with(actor, "t1", solved=True)


def test_list_rejects_an_unknown_status(client, uc):
    assert client.get("/api/teams/t1/issues?status=archived").status_code == 422
    uc.list_issues.assert_not_called()


def test_issue_response_shape(client, uc):
    uc.list_issues.return_value = [make_issue("i1", title="Slow hiring", priority=4, source_measurable_id="m1",
                                              source_week_start=__import__("datetime").date(2026, 11, 2))]
    issue = client.get("/api/teams/t1/issues").json()[0]
    assert issue == {
        "id": "i1", "team_id": "t1", "owner_id": "u2", "title": "Slow hiring", "priority": 4,
        "created_at": "2026-11-11T15:00:00Z", "solved_at": None, "resolution_note": None,
        "source_measurable_id": "m1", "source_week_start": "2026-11-02", "solved_in_meeting_id": None,
    }


# ---- create -----------------------------------------------------------------------------------

def test_create_returns_201_and_passes_clean_input(client, uc, actor):
    uc.create.return_value = make_issue("i9", title="Hello", priority=3)
    r = client.post("/api/teams/t1/issues", json={"title": "  Hello  ", "priority": 3})
    assert r.status_code == 201 and r.json()["id"] == "i9"
    uc.create.assert_called_once_with(actor, "t1", "Hello", 3)  # whitespace trimmed at the edge


def test_priority_is_optional_on_create(client, uc, actor):
    uc.create.return_value = make_issue()
    assert client.post("/api/teams/t1/issues", json={"title": "x"}).status_code == 201
    uc.create.assert_called_once_with(actor, "t1", "x", None)


@pytest.mark.parametrize(
    "body",
    [
        {}, {"title": ""}, {"title": "   "}, {"title": "x" * 301}, {"title": None},
        {"title": "ok", "priority": 0}, {"title": "ok", "priority": 6}, {"title": "ok", "priority": "high"},
        {"title": "ok", "priority": 2.5}, {"title": ["a"]},
    ],
)
def test_create_rejects_invalid_input_before_reaching_the_use_case(client, uc, body):
    assert client.post("/api/teams/t1/issues", json=body).status_code == 422
    uc.create.assert_not_called()


def test_title_at_the_length_limit_is_accepted(client, uc):
    uc.create.return_value = make_issue()
    assert client.post("/api/teams/t1/issues", json={"title": "x" * 300}).status_code == 201


@pytest.mark.parametrize("priority", [1, 5])
def test_priority_boundaries_are_accepted(client, uc, priority):
    uc.create.return_value = make_issue()
    assert client.post("/api/teams/t1/issues", json={"title": "x", "priority": priority}).status_code == 201


# ---- priority / solve ---------------------------------------------------------------------------

@pytest.mark.parametrize("priority", [1, 3, 5, None])
def test_set_priority_accepts_1_to_5_or_null_to_clear(client, uc, actor, priority):
    uc.set_priority.return_value = make_issue(priority=priority)
    assert client.patch("/api/issues/i1/priority", json={"priority": priority}).status_code == 200
    uc.set_priority.assert_called_once_with(actor, "i1", priority)


@pytest.mark.parametrize("body", [{}, {"priority": 0}, {"priority": 6}, {"priority": -1}, {"priority": "x"}])
def test_set_priority_rejects_invalid_input(client, uc, body):
    assert client.patch("/api/issues/i1/priority", json=body).status_code == 422
    uc.set_priority.assert_not_called()


def test_solve_requires_a_note_and_trims_it(client, uc, actor):
    uc.solve.return_value = make_issue(solved_at=NOW, resolution_note="Hired")
    r = client.post("/api/issues/i1/solve", json={"note": "  Hired  "})
    assert r.status_code == 200 and r.json()["resolution_note"] == "Hired" and r.json()["solved_at"]
    uc.solve.assert_called_once_with(actor, "i1", "Hired")


@pytest.mark.parametrize("body", [{}, {"note": ""}, {"note": "   "}, {"note": None}, {"note": "x" * 5001}])
def test_solve_rejects_a_missing_or_blank_note(client, uc, body):
    assert client.post("/api/issues/i1/solve", json=body).status_code == 422
    uc.solve.assert_not_called()


# ---- Make it an Issue ---------------------------------------------------------------------------

def test_make_it_an_issue_is_201_when_created_and_200_when_it_already_existed(client, uc, actor):
    uc.make_it_an_issue.return_value = (make_issue("i1"), True)
    first = client.post(f"/api/measurables/m1/scores/{W}/issue")
    uc.make_it_an_issue.return_value = (make_issue("i1"), False)
    again = client.post(f"/api/measurables/m1/scores/{W}/issue")
    assert (first.status_code, again.status_code) == (201, 200)
    assert first.json()["id"] == again.json()["id"] == "i1"
    uc.make_it_an_issue.assert_called_with(actor, "m1", __import__("datetime").date(2026, 11, 2))


@pytest.mark.parametrize("week", ["2026-13-01", "2026-02-30", "yesterday", "11-02-2026", "20261102x"])
def test_make_it_an_issue_rejects_a_bad_date(client, uc, week):
    assert client.post(f"/api/measurables/m1/scores/{week}/issue").status_code == 422
    uc.make_it_an_issue.assert_not_called()


def test_priority_with_seen_passes_it_on_and_without_it_does_not(client, uc, actor):
    uc.set_priority.return_value = make_issue("i1", priority=4)
    client.patch("/api/issues/i1/priority", json={"priority": 4})
    uc.set_priority.assert_called_with(actor, "i1", 4)
    client.patch("/api/issues/i1/priority", json={"priority": 4, "seen": None})
    uc.set_priority.assert_called_with(actor, "i1", 4, seen=None)
    client.patch("/api/issues/i1/priority", json={"priority": 4, "seen": 2})
    uc.set_priority.assert_called_with(actor, "i1", 4, seen=2)


def test_a_stale_priority_change_is_a_409_with_the_current_priority(client, uc):
    from app.core.errors import StaleDataError

    uc.set_priority.side_effect = StaleDataError("changed", current=5)
    r = client.patch("/api/issues/i1/priority", json={"priority": 4, "seen": 2})
    assert r.status_code == 409 and r.json()["current"] == 5 and r.json()["error"] == "stale_data"
