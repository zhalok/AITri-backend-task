"""Lost updates, against real Postgres with real parallel connections and real commits.

Ten editors who all looked at the same value save at the same moment. Exactly one may win; the other nine are
told the data is stale and write nothing, so no one's change is silently erased.
"""
import threading
import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.errors import StaleDataError
from app.modules.issue.models import Issue
from app.modules.issue.repository import IssueRepository
from app.modules.issue.service import IssueService
from app.modules.measurable.models import Measurable
from app.modules.score.models import Score
from app.modules.score.repository import ScoreRepository
from app.modules.team.models import Team
from app.modules.user.models import User
from tests.helpers import NOW, make_clock

WEEK = date(2026, 11, 2)
N = 10


@pytest.fixture
def committed(db_engine):
    """A team, user, Measurable and Issue that other connections can see; removed afterwards."""
    sfx = uuid.uuid4().hex[:8]
    ids = dict(team=f"lu_t_{sfx}", user=f"lu_u_{sfx}", meas=f"lu_m_{sfx}", issue=f"lu_i_{sfx}")
    with Session(db_engine) as s:
        s.add(Team(id=ids["team"], name="lu")); s.flush()
        s.add(User(id=ids["user"], name="u", email=f"{ids['user']}@t.test", role="team_member")); s.flush()
        s.add(Measurable(id=ids["meas"], team_id=ids["team"], owner_id=ids["user"], name="Deals", unit="n",
                         goal_type="at_least", goal_value=1)); s.flush()
        s.add(Issue(id=ids["issue"], team_id=ids["team"], owner_id=ids["user"], title="t", priority=2,
                    created_at=NOW)); s.commit()
    yield db_engine, ids
    with db_engine.begin() as c:
        for stmt in ("delete from issues where team_id = :team", "delete from scores where measurable_id = :meas",
                     "delete from measurables where team_id = :team", "delete from users where id = :user",
                     "delete from teams where id = :team"):
            c.execute(text(stmt), ids)


def race(work):
    """Run `work(i)` in N threads released together; returns the N outcomes ('won' or the error)."""
    barrier, out, lock = threading.Barrier(N), [], threading.Lock()

    def go(i):
        try:
            barrier.wait()
            outcome = work(i)
        except Exception as exc:  # recorded, asserted on by the callers
            outcome = exc
        with lock:
            out.append(outcome)

    threads = [threading.Thread(target=go, args=(i,)) for i in range(N)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    return out


def test_only_one_of_many_simultaneous_score_edits_based_on_the_same_value_wins(committed):
    engine, ids = committed
    with Session(engine) as s:
        ScoreRepository(s).upsert(ids["meas"], WEEK, Decimal(9)); s.commit()

    def save(i):
        with Session(engine) as s:
            saved = ScoreRepository(s).set_if_seen(ids["meas"], WEEK, Decimal(100 + i), Decimal(9))
            s.commit()
            return 100 + i if saved is not None else None

    results = race(save)
    winners = [r for r in results if isinstance(r, int)]
    assert len(winners) == 1 and results.count(None) == N - 1
    with Session(engine) as s:
        assert s.get(Score, (ids["meas"], WEEK)).value == Decimal(winners[0])  # the winner's value, nobody else's


def test_only_one_of_many_simultaneous_first_scores_for_an_empty_cell_wins(committed):
    engine, ids = committed

    def save(i):
        with Session(engine) as s:
            saved = ScoreRepository(s).set_if_seen(ids["meas"], WEEK, Decimal(100 + i), None)
            s.commit()
            return 100 + i if saved is not None else None

    results = race(save)
    winners = [r for r in results if isinstance(r, int)]
    assert len(winners) == 1 and results.count(None) == N - 1
    with Session(engine) as s:
        assert s.get(Score, (ids["meas"], WEEK)).value == Decimal(winners[0])


def test_only_one_of_many_simultaneous_priority_changes_based_on_the_same_value_wins(committed):
    engine, ids = committed

    def change(i):
        with Session(engine) as s:
            service = IssueService(IssueRepository(s), make_clock())
            try:
                service.set_priority(s.get(Issue, ids["issue"]), 3 + i % 3, seen=2)
                s.commit()
                return "won"
            except StaleDataError as exc:
                s.rollback()
                return exc

    results = race(change)
    assert results.count("won") == 1
    assert all(isinstance(r, StaleDataError) for r in results if r != "won")
    with Session(engine) as s:
        assert s.get(Issue, ids["issue"]).priority in (3, 4, 5)  # one of the attempted values, not the original 2


# ---- deterministic: hold the first editor's transaction open while the second one tries --------------------
# The ten-thread races above are a smoke test; the window is tiny. This one forces the interleaving, so it
# fails if the row lock is ever removed: without it the second editor reads the old value, passes the check,
# and overwrites the first editor's change as soon as that commits.

def second_editor_after_first_writes_but_before_it_commits(engine, first_write, second_write):
    """first_write(session) runs and stays uncommitted; second_write(session) runs in another thread meanwhile."""
    out = {}
    with Session(engine) as first:
        first_write(first)

        def second():
            with Session(engine) as s:
                out["result"] = second_write(s)
                s.commit()

        t = threading.Thread(target=second)
        t.start()
        t.join(timeout=0.7)  # the second editor must be waiting on the first one's lock, not finished
        assert t.is_alive(), "the second editor did not wait for the first editor's transaction"
        first.commit()
    t.join(timeout=5)
    assert not t.is_alive()
    return out["result"]


def test_a_second_score_editor_waits_for_the_first_and_is_then_refused(committed):
    engine, ids = committed
    with Session(engine) as s:
        ScoreRepository(s).upsert(ids["meas"], WEEK, Decimal(9)); s.commit()

    result = second_editor_after_first_writes_but_before_it_commits(
        engine,
        lambda s: ScoreRepository(s).set_if_seen(ids["meas"], WEEK, Decimal(100), Decimal(9)),
        lambda s: ScoreRepository(s).set_if_seen(ids["meas"], WEEK, Decimal(200), Decimal(9)),
    )
    assert result is None  # it saw 100 once the first committed, not the 9 it was told about
    with Session(engine) as s:
        assert s.get(Score, (ids["meas"], WEEK)).value == Decimal(100)  # the first editor's change survived


def test_a_second_priority_editor_waits_for_the_first_and_is_then_refused(committed):
    engine, ids = committed

    def first(s):
        IssueService(IssueRepository(s), make_clock()).set_priority(s.get(Issue, ids["issue"]), 5, seen=2)

    def second(s):
        try:
            IssueService(IssueRepository(s), make_clock()).set_priority(s.get(Issue, ids["issue"]), 1, seen=2)
            return "written"
        except StaleDataError as exc:
            return exc

    result = second_editor_after_first_writes_but_before_it_commits(engine, first, second)
    assert isinstance(result, StaleDataError) and result.extra == {"current": 5}
    with Session(engine) as s:
        assert s.get(Issue, ids["issue"]).priority == 5
