"""Access control (RBAC) over HTTP: what each ROLE may do, proven through the real app.

An Observer reads but never writes; a Team Member writes inside their team; only an Admin may use the wide
(/admin and company-wide) endpoints. Team *scope* (which team's data) is tested separately.
Users, from the seed: u1 admin, u3 team member and u5 observer (all of team_lead).
"""
import pytest

ADMIN, MEMBER, OBSERVER = "u1", "u3", "u5"

# (name, method, path, body, status when allowed). All on team_lead, where u3 and u5 are members.
WRITES = [
    ("edit a score", "PUT", "/measurables/m1/scores/2026-11-02", {"value": 5}, 200),
    ("make it an Issue", "POST", "/measurables/m1/scores/2026-10-05/issue", None, 201),  # off track, no Issue yet
    ("create an Issue", "POST", "/teams/team_lead/issues", {"title": "from a test"}, 201),
    ("set an Issue's priority", "PATCH", "/issues/i1/priority", {"priority": 3}, 200),
    ("solve an Issue", "POST", "/issues/i1/solve", {"note": "fixed"}, 200),
    ("add a To-Do", "POST", "/issues/i1/todos", {"title": "follow up", "owner_id": "u3"}, 201),
    ("mark a To-Do done", "POST", "/todos/t12/done", None, 200),
    ("undo a To-Do", "DELETE", "/todos/t1/done", None, 200),
    ("start a meeting", "POST", "/teams/team_lead/meetings", None, 201),
]
READS = [
    "/teams/team_lead", "/teams/team_lead/members", "/teams/team_lead/measurables", "/teams/team_lead/scorecard",
    "/teams/team_lead/issues", "/teams/team_lead/todos", "/teams/team_lead/todos/completion-rate",
    "/teams/team_lead/rocks", "/teams/team_lead/meetings/active", "/meetings/mt1", "/meetings/mt1/summary",
]
IDS = [w[0] for w in WRITES]


def snapshot(api):
    """What a refused write must not change."""
    r = lambda p: api.call(ADMIN, "GET", p).json()
    return (r("/admin/teams/team_lead/scorecard"), r("/admin/teams/team_lead/issues"),
            r("/admin/teams/team_lead/todos"), r("/admin/teams/team_lead/meetings/active"))


# ---- Observers: read, never write -------------------------------------------------------------

@pytest.mark.parametrize("name,method,path,body,_ok", WRITES, ids=IDS)
def test_an_observer_cannot_write(api, name, method, path, body, _ok):
    before = snapshot(api)
    r = api.call(OBSERVER, method, path, json=body)
    assert r.status_code == 403, f"{name}: {r.status_code} {r.text}"
    assert r.json()["error"] == "forbidden" and "observer" in r.json()["message"]
    assert snapshot(api) == before  # and nothing changed


@pytest.mark.parametrize("path", READS)
def test_an_observer_can_read(api, path):
    assert api.call(OBSERVER, "GET", path).status_code == 200


# ---- the same requests succeed for a Team Member, so the refusals above are about the role ---------

@pytest.mark.parametrize("name,method,path,body,ok", WRITES, ids=IDS)
def test_a_team_member_can_write_in_their_team(api, name, method, path, body, ok):
    r = api.call(MEMBER, method, path, json=body)
    assert r.status_code == ok, f"{name}: {r.status_code} {r.text}"


def test_an_observer_can_join_a_meeting_but_not_run_it(api):
    started = api.call("u2", "POST", "/teams/team_lead/meetings")
    meeting = started.json()["id"]
    assert api.call(OBSERVER, "POST", f"/meetings/{meeting}/join").status_code == 200  # joining is a read-level action
    for method, path, body in (("POST", f"/meetings/{meeting}/advance", None), ("POST", f"/meetings/{meeting}/end", None),
                               ("PUT", f"/meetings/{meeting}/rating", {"rating": 7})):
        assert api.call(OBSERVER, method, path, json=body).status_code == 403, path


def test_only_the_facilitator_may_advance_or_end_a_meeting(api):
    meeting = api.call("u2", "POST", "/teams/team_lead/meetings").json()["id"]  # u2 is the facilitator
    assert api.call(MEMBER, "POST", f"/meetings/{meeting}/advance").status_code == 403  # a Team Member, but not the facilitator
    assert api.call(MEMBER, "POST", f"/meetings/{meeting}/end").status_code == 403
    assert api.call("u2", "POST", f"/meetings/{meeting}/advance").status_code == 200


# ---- wide endpoints: Admin only ---------------------------------------------------------------

ADMIN_ONLY_GETS = [
    "/admin/teams/team_lead", "/admin/teams/team_ops/scorecard", "/admin/teams/team_sales/issues",
    "/admin/teams/team_ops/todos", "/admin/teams/team_sales/rocks", "/admin/teams/team_lead/members",
    "/admin/teams/team_lead/meetings/active", "/admin/meetings/mt1", "/admin/meetings/mt1/summary",
    "/teams/all", "/users/all", "/audit-events",
]


@pytest.mark.parametrize("path", ADMIN_ONLY_GETS)
@pytest.mark.parametrize("user", [MEMBER, OBSERVER, "u2"])
def test_wide_endpoints_refuse_everyone_but_admins(api, user, path):
    r = api.call(user, "GET", path)
    assert r.status_code == 403 and r.json()["error"] == "forbidden", f"{user} {path}: {r.status_code}"


@pytest.mark.parametrize("path", ADMIN_ONLY_GETS)
def test_an_admin_may_use_them(api, path):
    assert api.call(ADMIN, "GET", path).status_code == 200


def test_an_admin_can_write_in_a_team_they_do_not_belong_to_through_the_wide_endpoints(api):
    # u1 belongs to team_lead only; team_ops' scorecard is reached through /admin, never the narrow route
    assert api.call(ADMIN, "PUT", "/admin/measurables/m7/scores/2026-11-02", json={"value": 4}).status_code == 200
    assert api.call(ADMIN, "PUT", "/measurables/m7/scores/2026-11-02", json={"value": 4}).status_code == 403
    assert api.call(MEMBER, "PUT", "/admin/measurables/m1/scores/2026-11-02", json={"value": 4}).status_code == 403


# ---- authentication comes first -----------------------------------------------------------------

@pytest.mark.parametrize("name,method,path,body,_ok", WRITES, ids=IDS)
def test_no_token_is_401_before_anything_else(api, name, method, path, body, _ok):
    assert api.call(None, method, path, json=body).status_code == 401


def test_a_forged_token_is_401(api):
    r = api.client.get("/api/teams/team_lead/scorecard", headers={"Authorization": "Bearer not.a.token"})
    assert r.status_code == 401


def test_signing_in_as_an_unknown_email_is_401(api):
    assert api.client.post("/api/auth/login", json={"email": "nobody@acme.test"}).status_code == 401


def test_make_it_an_issue_on_a_cell_that_already_has_one_returns_it_instead_of_a_duplicate(api):
    # the seed already has an unsolved Issue (i5) for Measurable m1, week of Nov 2
    r = api.call(MEMBER, "POST", "/measurables/m1/scores/2026-11-02/issue")
    assert r.status_code == 200 and r.json()["id"] == "i5"
    assert len([i for i in api.call(MEMBER, "GET", "/teams/team_lead/issues").json() if i["source_week_start"] == "2026-11-02"
                and i["source_measurable_id"] == "m1"]) == 1


def test_make_it_an_issue_on_a_cell_that_is_not_off_track_is_refused(api):
    # m1 for the week of Oct 19 is on track
    r = api.call(MEMBER, "POST", "/measurables/m1/scores/2026-10-19/issue")
    assert r.status_code == 422
