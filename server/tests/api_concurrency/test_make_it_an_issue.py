"""Concurrent 'Make it an Issue' on the same Measurable + week must leave exactly one Issue (brief 2.6 / 2.8)."""
import threading

from sqlalchemy import text

# m1 "New deals closed" (goal >= 10), week of 2026-10-05 scored 8: off-track, and the seed has no Issue for it.
CELL = "/measurables/m1/scores/2026-10-05/issue"
CALLERS = ["u2", "u3", "u4"]  # three different team members click at the same moment


def fire_together(api, path, users):
    """Send one request per user at the same instant (all threads wait on a barrier, then go)."""
    start = threading.Barrier(len(users))
    results = [None] * len(users)

    def click(i, user):
        start.wait()
        results[i] = api.call(user, "POST", path)

    for u in users:
        api.token(u)  # sign in first so the race is only about the Issue
    threads = [threading.Thread(target=click, args=(i, u)) for i, u in enumerate(users)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    return results


def unsolved_rows(engine, week="2026-10-05"):
    with engine.connect() as c:
        return c.execute(text(
            "select id, owner_id from issues where source_measurable_id = 'm1' "
            "and source_week_start = :w and solved_at is null"), {"w": week}).all()


def test_simultaneous_clicks_create_one_issue_and_the_rest_get_it_back(race_api):
    api, engine = race_api
    assert unsolved_rows(engine) == []  # precondition: nothing yet for this cell

    responses = fire_together(api, CELL, CALLERS)

    assert [r.status_code for r in responses].count(201) == 1      # exactly one request created it
    assert [r.status_code for r in responses].count(200) == len(CALLERS) - 1  # the others got the existing one
    assert len({r.json()["id"] for r in responses}) == 1           # all three answers are the same Issue
    rows = unsolved_rows(engine)
    assert len(rows) == 1                                          # and the database holds one row
    assert rows[0].id == responses[0].json()["id"]
    creator = next(u for u, r in zip(CALLERS, responses) if r.status_code == 201)
    assert rows[0].owner_id == creator                             # owned by whoever actually created it


def test_after_it_is_solved_the_cell_can_be_made_an_issue_again(race_api):
    api, engine = race_api
    first = unsolved_rows(engine)[0].id  # left by the previous test (same module database)
    assert api.call("u2", "POST", f"/issues/{first}/solve", json={"note": "handled"}).status_code == 200

    responses = fire_together(api, CELL, CALLERS)

    assert [r.status_code for r in responses].count(201) == 1
    new_ids = {r.json()["id"] for r in responses}
    assert len(new_ids) == 1 and first not in new_ids              # a fresh Issue, not the solved one
    assert len(unsolved_rows(engine)) == 1
