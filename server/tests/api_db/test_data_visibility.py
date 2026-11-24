"""Data visibility (team scope) over HTTP, against a real database: which team's data each user can see.

Expected answers come from the seed's membership list, not from the app. Role-based access is tested in
tests/api/test_access_control.py; this is the other half: a user with the right role is still refused another
team's data, even by a guessed id.
"""
import pytest

from tests.api_db.conftest import SEED

MEMBER_OF = {(m["user_id"], m["team_id"]) for m in SEED["memberships"]}
USERS = sorted(u["id"] for u in SEED["users"])
TEAMS = sorted(t["id"] for t in SEED["teams"])
ROLE = {u["id"]: u["role"] for u in SEED["users"]}

TEAM_READS = ["", "/members", "/measurables", "/scorecard", "/issues", "/issues?status=solved", "/todos",
              "/todos/completion-rate", "/rocks", "/meetings/active"]


def teams_of(user):
    return {t for (u, t) in MEMBER_OF if u == user}


def people_sharing_a_team_with(user):
    mine = teams_of(user)
    return {u for (u, t) in MEMBER_OF if t in mine}


def first(table, team):
    return next(r["id"] for r in SEED[table] if r["team_id"] == team)


# ---- every user x every team x every team-scoped read --------------------------------------------

@pytest.mark.parametrize("suffix", TEAM_READS)
@pytest.mark.parametrize("team", TEAMS)
@pytest.mark.parametrize("user", USERS)
def test_a_user_reads_a_team_only_if_they_belong_to_it(live, user, team, suffix):
    status = live.call(user, "GET", f"/teams/{team}{suffix}").status_code
    assert status == (200 if (user, team) in MEMBER_OF else 403), f"{user} ({ROLE[user]}) on {team}{suffix}"


def test_membership_not_role_decides_even_for_an_admin(live):
    # u1 is an Admin but belongs only to team_lead: the narrow route refuses the other teams, /admin allows them
    assert live.call("u1", "GET", "/teams/team_lead/scorecard").status_code == 200
    assert live.call("u1", "GET", "/teams/team_ops/scorecard").status_code == 403
    assert live.call("u1", "GET", "/admin/teams/team_ops/scorecard").status_code == 200


@pytest.mark.parametrize("team", TEAMS)
def test_an_admin_sees_every_team_through_the_wide_endpoints(live, team):
    for suffix in TEAM_READS:
        assert live.call("u1", "GET", f"/admin/teams/{team}{suffix}").status_code == 200, suffix


# ---- what comes back is only that team's data ---------------------------------------------------

@pytest.mark.parametrize("team", TEAMS)
def test_a_teams_data_contains_nothing_from_other_teams(live, team):
    member = next(u for u in USERS if (u, team) in MEMBER_OF)
    get = lambda p: live.call(member, "GET", f"/teams/{team}{p}").json()
    assert {r["measurable"]["team_id"] for r in get("/scorecard")["rows"]} <= {team}
    assert {i["team_id"] for i in get("/issues") + get("/issues?status=solved")} <= {team}
    assert {t["team_id"] for t in get("/todos")} <= {team}
    assert {r["team_id"] for r in get("/rocks")} <= {team}
    assert {m["team_id"] for m in get("/measurables")} <= {team}
    assert {u["id"] for u in get("/members")} <= {u for (u, t) in MEMBER_OF if t == team}


@pytest.mark.parametrize("user", USERS)
def test_a_user_lists_only_their_own_teams(live, user):
    assert {t["id"] for t in live.call(user, "GET", "/teams").json()} == teams_of(user)


@pytest.mark.parametrize("user", USERS)
def test_a_user_lists_only_people_who_share_a_team_with_them(live, user):
    assert {u["id"] for u in live.call(user, "GET", "/users").json()} == people_sharing_a_team_with(user)


def test_a_member_of_two_teams_sees_both_and_nothing_else(live):
    assert teams_of("u2") == {"team_lead", "team_sales"}
    assert {t["id"] for t in live.call("u2", "GET", "/teams").json()} == {"team_lead", "team_sales"}
    assert live.call("u2", "GET", "/teams/team_ops").status_code == 403


# ---- meetings belong to a team too --------------------------------------------------------------

@pytest.mark.parametrize("meeting", [m["id"] for m in SEED["meetings"]])
@pytest.mark.parametrize("user", USERS)
def test_a_meeting_and_its_summary_are_visible_only_to_its_teams_members(live, user, meeting):
    team = next(m["team_id"] for m in SEED["meetings"] if m["id"] == meeting)
    expected = 200 if (user, team) in MEMBER_OF else 403
    assert live.call(user, "GET", f"/meetings/{meeting}").status_code == expected
    assert live.call(user, "GET", f"/meetings/{meeting}/summary").status_code == expected


# ---- guessing ids does not help -------------------------------------------------------------------

def test_a_team_that_does_not_exist_looks_the_same_as_one_you_may_not_see(live):
    ghost = live.call("u8", "GET", "/teams/no_such_team/scorecard")
    forbidden = live.call("u8", "GET", "/teams/team_lead/scorecard")
    assert ghost.status_code == forbidden.status_code == 403
    assert ghost.json() == forbidden.json()  # nothing reveals whether the id exists


# ---- writes are scoped too: the right role, the wrong team -------------------------------------------

def attempts_on(team, measurable):
    """Writes aimed at another team's records."""
    issue, todo = first("issues", team), first("todos", team)
    return [
        ("edit a score", "PUT", f"/measurables/{measurable}/scores/2026-11-02", {"value": 5}),
        ("make it an Issue", "POST", f"/measurables/{measurable}/scores/2026-11-02/issue", None),
        ("create an Issue", "POST", f"/teams/{team}/issues", {"title": "intruder"}),
        ("set priority", "PATCH", f"/issues/{issue}/priority", {"priority": 1}),
        ("solve an Issue", "POST", f"/issues/{issue}/solve", {"note": "intruder"}),
        ("add a To-Do", "POST", f"/issues/{issue}/todos", {"title": "intruder", "owner_id": "u8"}),
        ("mark a To-Do done", "POST", f"/todos/{todo}/done", None),
        ("undo a To-Do", "DELETE", f"/todos/{todo}/done", None),
        ("start a meeting", "POST", f"/teams/{team}/meetings", None),
    ]


def state_of(live, team):
    get = lambda p: live.call("u1", "GET", f"/admin/teams/{team}{p}").json()
    return get("/scorecard"), get("/issues"), get("/issues?status=solved"), get("/todos"), get("/meetings/active")


@pytest.mark.parametrize("intruder,team,measurable", [("u3", "team_ops", "m7"), ("u8", "team_lead", "m1"), ("u6", "team_ops", "m7")])
def test_a_team_member_cannot_write_into_another_teams_data(live, intruder, team, measurable):
    before = state_of(live, team)
    for name, method, path, body in attempts_on(team, measurable):
        r = live.call(intruder, method, path, json=body)
        assert r.status_code == 403, f"{intruder} -> {team}: {name} gave {r.status_code} {r.text}"
    assert state_of(live, team) == before  # not one change got through
