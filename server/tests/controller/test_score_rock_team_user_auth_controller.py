from datetime import date
from decimal import Decimal

import pytest

from app.modules.auth.factory import get_auth_usecase
from app.modules.auth.service import LoginResult
from app.modules.measurable.factory import get_measurable_usecase
from app.modules.rock.factory import get_rock_usecase
from app.modules.rock.service import RockDetail
from app.modules.score.factory import get_score_usecase
from app.modules.score.models import Score
from app.modules.score.service import Scorecard, ScorecardLine
from app.modules.team.factory import get_team_usecase
from app.modules.user.factory import get_user_usecase
from tests.helpers import make_measurable, make_milestone, make_rock, make_team, make_user

W1, W2 = date(2026, 11, 2), date(2026, 11, 9)


# ---- scorecard / scores -------------------------------------------------------------------------

def test_scorecard_shape_maps_weeks_to_scores_with_nulls_for_missing(client, mock_usecase, actor):
    uc = mock_usecase(get_score_usecase)
    uc.get_scorecard.return_value = Scorecard(
        weeks=[W1, W2],
        lines=[ScorecardLine(make_measurable("m1"), {W1: Decimal("12"), W2: None}, {W1: "on_track", W2: "off_track"})],
    )
    body = client.get("/api/teams/t1/scorecard").json()
    assert body["weeks"] == ["2026-11-02", "2026-11-09"]
    row = body["rows"][0]
    assert row["measurable"]["id"] == "m1" and row["measurable"]["goal_type"] == "at_least"
    assert float(row["scores"]["2026-11-02"]) == 12 and row["scores"]["2026-11-09"] is None
    uc.get_scorecard.assert_called_once_with(actor, "t1")


def test_set_score_passes_a_decimal_and_returns_the_saved_score(client, mock_usecase, actor):
    uc = mock_usecase(get_score_usecase)
    uc.set_score.return_value = Score(measurable_id="m1", week_start=W1, value=Decimal("12.5"))
    r = client.put("/api/measurables/m1/scores/2026-11-02", json={"value": 12.5})
    assert r.status_code == 200
    assert (r.json()["measurable_id"], r.json()["week_start"]) == ("m1", "2026-11-02") and float(r.json()["value"]) == 12.5
    uc.set_score.assert_called_once_with(actor, "m1", W1, Decimal("12.5"))


@pytest.mark.parametrize("value", [0, -5, 0.0001, 1234567890123.5])
def test_set_score_accepts_zero_negative_and_precise_numbers(client, mock_usecase, value):
    uc = mock_usecase(get_score_usecase)
    uc.set_score.return_value = Score(measurable_id="m1", week_start=W1, value=Decimal(str(value)))
    assert client.put("/api/measurables/m1/scores/2026-11-02", json={"value": value}).status_code == 200


@pytest.mark.parametrize("body", [{}, {"value": None}, {"value": "abc"}, {"value": "NaN"}, {"value": "Infinity"},
                                  {"value": 1.23456}, {"value": 10 ** 15}, {"value": [1]}])
def test_set_score_rejects_non_numbers_and_out_of_range(client, mock_usecase, body):
    uc = mock_usecase(get_score_usecase)
    assert client.put("/api/measurables/m1/scores/2026-11-02", json=body).status_code == 422
    uc.set_score.assert_not_called()


@pytest.mark.parametrize("week", ["2026-13-01", "nope", "2026-11"])
def test_set_score_rejects_a_bad_week(client, mock_usecase, week):
    uc = mock_usecase(get_score_usecase)
    assert client.put(f"/api/measurables/m1/scores/{week}", json={"value": 1}).status_code == 422
    uc.set_score.assert_not_called()


def test_measurables_list(client, mock_usecase, actor):
    uc = mock_usecase(get_measurable_usecase)
    uc.list_for_team.return_value = [make_measurable("m1"), make_measurable("m2", goal_type="between",
                                     goal_value=None, goal_min=Decimal(2), goal_max=Decimal(4))]
    body = client.get("/api/teams/t1/measurables").json()
    assert [m["id"] for m in body] == ["m1", "m2"]
    assert (body[1]["goal_type"], body[1]["goal_value"]) == ("between", None)
    assert float(body[1]["goal_min"]) == 2 and float(body[1]["goal_max"]) == 4


# ---- rocks --------------------------------------------------------------------------------------

def test_rocks_come_back_with_their_milestones_nested(client, mock_usecase, actor):
    uc = mock_usecase(get_rock_usecase)
    uc.list_current_rocks.return_value = [
        RockDetail(make_rock("r1"), [make_milestone("ms1", done=True), make_milestone("ms2", due_date=date(2026, 12, 15))]),
        RockDetail(make_rock("r2", status="complete"), []),
    ]
    rocks = client.get("/api/teams/t1/rocks").json()
    assert [r["id"] for r in rocks] == ["r1", "r2"]
    assert [(m["id"], m["done"], m["due_date"]) for m in rocks[0]["milestones"]] == [
        ("ms1", True, "2026-12-01"), ("ms2", False, "2026-12-15")]
    assert rocks[1]["milestones"] == [] and rocks[1]["status"] == "complete"
    assert set(rocks[0]) == {"id", "team_id", "owner_id", "title", "quarter", "status", "milestones"}
    uc.list_current_rocks.assert_called_once_with(actor, "t1")


# ---- teams / users ----------------------------------------------------------------------------------

def test_teams_default_route_is_my_teams_and_all_is_its_own_route(client, mock_usecase, actor):
    uc = mock_usecase(get_team_usecase)
    uc.list_my_teams.return_value = [make_team("t1", "Leadership")]
    uc.list_all_teams.return_value = [make_team("t1", "Leadership"), make_team("t2", "Sales")]
    assert [t["id"] for t in client.get("/api/teams").json()] == ["t1"]
    assert [t["id"] for t in client.get("/api/teams/all").json()] == ["t1", "t2"]
    uc.get_team.assert_not_called()  # "all" is not mistaken for a team id
    uc.list_my_teams.assert_called_once_with(actor)
    uc.list_all_teams.assert_called_once_with(actor)


def test_team_members(client, mock_usecase, actor):
    uc = mock_usecase(get_team_usecase)
    uc.list_assignable_members.return_value = [make_user("u1", "admin"), make_user("u2")]
    body = client.get("/api/teams/t1/members").json()
    assert [(u["id"], u["role"]) for u in body] == [("u1", "admin"), ("u2", "team_member")]
    assert set(body[0]) == {"id", "name", "email", "role"}  # nothing else leaks


def test_users_default_route_is_colleagues_and_all_is_its_own_route(client, mock_usecase, actor):
    uc = mock_usecase(get_user_usecase)
    uc.list_users.return_value = [make_user("u2")]
    uc.list_all_users.return_value = [make_user("u1", "admin"), make_user("u2")]
    assert len(client.get("/api/users").json()) == 1
    assert len(client.get("/api/users/all").json()) == 2
    uc.list_users.assert_called_once_with(actor)
    uc.list_all_users.assert_called_once_with(actor)


# ---- auth ---------------------------------------------------------------------------------------

def test_login_returns_a_token_response(client, mock_usecase):
    uc = mock_usecase(get_auth_usecase)
    uc.login.return_value = LoginResult(access_token="tok", expires_in=28800, user=make_user("u2", email="blake@acme.test"))
    r = client.post("/api/auth/login", json={"email": "  blake@acme.test "})
    assert r.status_code == 200
    assert r.json() == {"access_token": "tok", "token_type": "bearer", "expires_in": 28800,
                        "user": {"id": "u2", "name": "User u2", "email": "blake@acme.test", "role": "team_member"}}
    uc.login.assert_called_once_with("blake@acme.test")  # padding trimmed at the edge


@pytest.mark.parametrize("body", [{}, {"email": ""}, {"email": "ab"}, {"email": None}, {"email": "a" * 321}, {"password": "x"}])
def test_login_rejects_invalid_input(client, mock_usecase, body):
    uc = mock_usecase(get_auth_usecase)
    assert client.post("/api/auth/login", json=body).status_code == 422
    uc.login.assert_not_called()


def test_me_returns_the_authenticated_user(client, actor):
    r = client.get("/api/auth/me")
    assert r.status_code == 200 and r.json()["id"] == actor.id
