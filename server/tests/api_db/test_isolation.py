"""The real-database API tests share one seeded database; a test's writes must vanish when it ends."""
from tests.api_db.conftest import SEED

SEEDED_ISSUES = len([i for i in SEED["issues"] if i["team_id"] == "team_lead"])


def issues(live):
    return live.call("u3", "GET", "/teams/team_lead/issues").json() + live.call("u3", "GET", "/teams/team_lead/issues?status=solved").json()


def test_first_a_test_writes(live):
    assert live.call("u3", "POST", "/teams/team_lead/issues", json={"title": "left behind?"}).status_code == 201
    assert len(issues(live)) == SEEDED_ISSUES + 1


def test_then_the_next_test_sees_the_pristine_seed(live):
    assert len(issues(live)) == SEEDED_ISSUES
    assert "left behind?" not in [i["title"] for i in issues(live)]
