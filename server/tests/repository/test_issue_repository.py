import threading
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.issue.models import Issue
from app.modules.issue.repository import IssueRepository
from app.modules.measurable.models import Measurable
from tests.helpers import NOW, make_issue, make_measurable
from tests.repository.conftest import add, violates

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
W = date(2026, 11, 2)  # a Monday


def issue(id, **kw):
    kw.setdefault("created_at", T0)
    return make_issue(id=id, **kw)


@pytest.fixture
def repo(world):
    return IssueRepository(world)


@pytest.fixture
def m1(world):
    return add(world, make_measurable("m1", team_id="t1", owner_id="u2"))


def values(**kw):
    base = dict(id=uuid.uuid4().hex, team_id="t1", owner_id="u2", title="Deals — week of 2026-11-02", priority=None,
                created_at=NOW, source_measurable_id="m1", source_week_start=W)
    return {**base, **kw}


# ---- Issue order: priority 5 -> 1, no priority last, oldest first within a priority -------------------

def test_unsolved_issue_order(world, repo):
    add(world,
        issue("p3_old", priority=3), issue("p5_new", priority=5, created_at=T0 + timedelta(hours=2)),
        issue("p5_old", priority=5), issue("none_oldest", priority=None, created_at=T0 - timedelta(days=1)),
        issue("p3_new", priority=3, created_at=T0 + timedelta(hours=1)), issue("p1", priority=1),
        issue("none_new", priority=None, created_at=T0 + timedelta(days=1)))
    assert [i.id for i in repo.list_unsolved("t1")] == [
        "p5_old", "p5_new", "p3_old", "p3_new", "p1", "none_oldest", "none_new"]


def test_same_priority_and_time_falls_back_to_id_so_the_order_is_stable(world, repo):
    add(world, issue("b", priority=2), issue("a", priority=2), issue("c", priority=2))
    assert [i.id for i in repo.list_unsolved("t1")] == ["a", "b", "c"]


def test_unsolved_excludes_solved_and_other_teams(world, repo):
    add(world, issue("open"), issue("done", solved_at=NOW, resolution_note="ok"), issue("other", team_id="t2"))
    assert [i.id for i in repo.list_unsolved("t1")] == ["open"]


def test_solved_list_is_newest_solve_first_and_excludes_open_and_other_teams(world, repo):
    add(world,
        issue("s_old", solved_at=T0, resolution_note="a"), issue("s_new", solved_at=T0 + timedelta(days=1), resolution_note="b"),
        issue("open"), issue("s_other", team_id="t2", solved_at=T0, resolution_note="c"))
    assert [i.id for i in repo.list_solved("t1")] == ["s_new", "s_old"]


# ---- source lookup and the no-duplicates insert -------------------------------------------------------

def test_find_unsolved_by_source(world, repo, m1):
    add(world, issue("hit", source_measurable_id="m1", source_week_start=W),
        issue("solved", source_measurable_id="m1", source_week_start=date(2026, 10, 26), solved_at=NOW, resolution_note="x"))
    assert repo.find_unsolved_by_source("m1", W).id == "hit"
    assert repo.find_unsolved_by_source("m1", date(2026, 10, 26)) is None  # solved does not count
    assert repo.find_unsolved_by_source("m1", date(2026, 11, 9)) is None
    assert repo.find_unsolved_by_source("nope", W) is None


def test_insert_from_source_inserts_once_then_reports_the_conflict(world, repo, m1):
    assert repo.insert_from_source_if_absent(values()) is True
    assert repo.insert_from_source_if_absent(values()) is False  # different id, same (measurable, week)
    world.expire_all()
    assert world.query(Issue).filter_by(source_measurable_id="m1").count() == 1


def test_a_solved_issue_frees_the_slot_for_a_new_one(world, repo, m1):
    repo.insert_from_source_if_absent(values())
    first = repo.find_unsolved_by_source("m1", W)
    first.solved_at, first.resolution_note = NOW, "fixed"
    world.flush()
    assert repo.insert_from_source_if_absent(values()) is True
    assert repo.find_unsolved_by_source("m1", W).id != first.id


def test_other_weeks_and_measurables_do_not_collide(world, repo, m1):
    add(world, make_measurable("m2", team_id="t1", owner_id="u2"))
    assert repo.insert_from_source_if_absent(values()) is True
    assert repo.insert_from_source_if_absent(values(source_week_start=date(2026, 11, 9))) is True
    assert repo.insert_from_source_if_absent(values(source_measurable_id="m2")) is True


# ---- the database rejects invalid issues (not only the app) ---------------------------------------------

@pytest.mark.parametrize("priority", [0, 6, -1, 100])
def test_priority_must_be_1_to_5(world, priority):
    violates(world, issue("bad", priority=priority))


@pytest.mark.parametrize("priority", [None, 1, 5])
def test_valid_priorities_are_stored(world, repo, priority):
    add(world, issue("ok", priority=priority))
    assert repo.get("ok").priority == priority


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_title_cannot_be_blank(world, title):
    violates(world, issue("bad", title=title))


def test_solved_requires_a_note_and_a_note_requires_solved(world):
    violates(world, issue("a", solved_at=NOW))                                   # solved, no note
    violates(world, issue("b", resolution_note="orphan note"))                  # note, not solved
    violates(world, issue("c", solved_at=NOW, resolution_note="   "))           # blank note


def test_source_is_a_measurable_and_week_together(world, m1):
    violates(world, issue("a", source_measurable_id="m1"))
    violates(world, issue("b", source_week_start=W))


@pytest.mark.parametrize("week", [date(2026, 11, 3), date(2026, 11, 8)])
def test_source_week_must_be_a_monday(world, m1, week):
    violates(world, issue("bad", source_measurable_id="m1", source_week_start=week))


def test_two_unsolved_issues_for_the_same_source_are_rejected_by_the_index_itself(world, m1):
    add(world, issue("first", source_measurable_id="m1", source_week_start=W))
    violates(world, issue("second", source_measurable_id="m1", source_week_start=W))


def test_solved_duplicates_of_a_source_may_coexist(world, m1):
    add(world, issue("s1", source_measurable_id="m1", source_week_start=W, solved_at=NOW, resolution_note="a"),
        issue("s2", source_measurable_id="m1", source_week_start=W, solved_at=NOW, resolution_note="b"),
        issue("open", source_measurable_id="m1", source_week_start=W))


def test_foreign_keys_are_enforced(world):
    violates(world, issue("a", team_id="no_such_team"))
    violates(world, issue("b", owner_id="no_such_user"))


# ---- concurrency: real parallel connections, real commits -------------------------------------------------

def test_concurrent_make_it_an_issue_creates_exactly_one_issue(db_engine):
    suffix = uuid.uuid4().hex[:8]
    team, user, meas = f"race_t_{suffix}", f"race_u_{suffix}", f"race_m_{suffix}"
    from app.modules.team.models import Team
    from app.modules.user.models import User

    with Session(db_engine) as s:  # committed setup, visible to the other connections
        s.add(Team(id=team, name="race")); s.flush()
        s.add(User(id=user, name="r", email=f"{user}@t.test", role="team_member")); s.flush()
        s.add(Measurable(id=meas, team_id=team, owner_id=user, name="Deals", unit="n", goal_type="at_least",
                         goal_value=1)); s.commit()
    n, barrier, results, errors = 12, threading.Barrier(12), [], []

    def click():
        try:
            with Session(db_engine) as s:
                repo = IssueRepository(s)
                barrier.wait()  # everyone fires at the same moment
                inserted = repo.insert_from_source_if_absent(values(
                    id=uuid.uuid4().hex, team_id=team, owner_id=user, source_measurable_id=meas))
                found = repo.find_unsolved_by_source(meas, W)
                s.commit()
                results.append((inserted, found.id))
        except Exception as exc:  # pragma: no cover - surfaced by the assertions below
            errors.append(exc)

    try:
        threads = [threading.Thread(target=click) for _ in range(n)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        assert errors == []
        assert sum(1 for inserted, _ in results if inserted) == 1          # exactly one writer won
        assert len({issue_id for _, issue_id in results}) == 1              # all n callers see the same Issue
        with Session(db_engine) as s:
            assert s.query(Issue).filter_by(source_measurable_id=meas).count() == 1
    finally:
        with db_engine.begin() as c:
            for stmt in ("delete from issues where team_id = :t", "delete from measurables where team_id = :t",
                         "delete from users where id = :u", "delete from teams where id = :t"):
                c.execute(text(stmt), {"t": team, "u": user})
