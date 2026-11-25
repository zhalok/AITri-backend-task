from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.modules.measurable.repository import MeasurableRepository
from app.modules.milestone.repository import MilestoneRepository
from app.modules.rock.repository import RockRepository
from app.modules.score.models import Score
from app.modules.score.repository import ScoreRepository
from tests.helpers import make_measurable, make_milestone, make_rock
from tests.repository.conftest import add, violates

W1, W2, W3 = date(2026, 10, 26), date(2026, 11, 2), date(2026, 11, 9)  # Mondays


# ---- scores -----------------------------------------------------------------------------------

@pytest.fixture
def scores(world):
    add(world, make_measurable("m1", owner_id="u2"), make_measurable("m2", owner_id="u2"))
    return ScoreRepository(world)


def test_upsert_inserts_a_new_score(scores, world):
    saved = scores.upsert("m1", W1, Decimal("12.5"))
    assert (saved.measurable_id, saved.week_start, saved.value) == ("m1", W1, Decimal("12.5000"))
    assert world.query(Score).count() == 1


def test_upsert_overwrites_so_the_last_save_wins_and_never_duplicates(scores, world):
    scores.upsert("m1", W1, Decimal(5))
    scores.upsert("m1", W1, Decimal(9))
    final = scores.upsert("m1", W1, Decimal("7.25"))
    assert final.value == Decimal("7.25")
    assert world.query(Score).filter_by(measurable_id="m1", week_start=W1).count() == 1


def test_upsert_accepts_zero_and_negative_values(scores):
    assert scores.upsert("m1", W1, Decimal(0)).value == 0
    assert scores.upsert("m1", W2, Decimal("-3")).value == -3


def test_list_for_filters_by_measurable_and_week(scores):
    for m, w, v in [("m1", W1, 1), ("m1", W2, 2), ("m1", W3, 3), ("m2", W1, 4)]:
        scores.upsert(m, w, Decimal(v))
    got = {(s.measurable_id, s.week_start): s.value for s in scores.list_for(["m1"], [W1, W2])}
    assert got == {("m1", W1): 1, ("m1", W2): 2}
    assert scores.list_for([], [W1]) == []


@pytest.mark.parametrize("week", [date(2026, 11, 3), date(2026, 11, 8), date(2026, 11, 1)])
def test_a_score_week_must_be_a_monday_in_the_database(scores, world, week):
    violates(world, Score(measurable_id="m1", week_start=week, value=Decimal(1)))


def test_a_score_needs_an_existing_measurable(world):
    violates(world, Score(measurable_id="ghost", week_start=W1, value=Decimal(1)))


def test_a_measurables_score_for_a_week_is_unique(scores, world):
    add(world, Score(measurable_id="m1", week_start=W1, value=Decimal(1)))
    violates(world, Score(measurable_id="m1", week_start=W1, value=Decimal(2)))


# ---- measurables ------------------------------------------------------------------------------

def test_measurables_are_listed_per_team_in_id_order(world):
    add(world, make_measurable("m_b", team_id="t1", owner_id="u2"), make_measurable("m_a", team_id="t1", owner_id="u2"),
        make_measurable("m_x", team_id="t2", owner_id="u2"))
    assert [m.id for m in MeasurableRepository(world).list_for_team("t1")] == ["m_a", "m_b"]
    assert MeasurableRepository(world).list_for_team("nobody") == []


@pytest.mark.parametrize(
    "goal",
    [
        dict(goal_type="at_least", goal_value=Decimal(10)),
        dict(goal_type="at_most", goal_value=Decimal("3.5")),
        dict(goal_type="exactly", goal_value=Decimal(1)),
        dict(goal_type="between", goal_value=None, goal_min=Decimal(2), goal_max=Decimal(4)),
        dict(goal_type="between", goal_value=None, goal_min=Decimal(3), goal_max=Decimal(3)),  # min == max is fine
    ],
)
def test_every_goal_shape_is_accepted(world, goal):
    add(world, make_measurable("ok", owner_id="u2", **goal))


@pytest.mark.parametrize(
    "goal",
    [
        dict(goal_type="sometimes", goal_value=Decimal(1)),                                   # unknown type
        dict(goal_type="at_least", goal_value=None),                                          # needs a value
        dict(goal_type="at_least", goal_value=Decimal(1), goal_min=Decimal(0)),               # stray min
        dict(goal_type="between", goal_value=None),                                           # needs min and max
        dict(goal_type="between", goal_value=None, goal_min=Decimal(1)),                      # needs max too
        dict(goal_type="between", goal_value=Decimal(1), goal_min=Decimal(1), goal_max=Decimal(2)),  # stray value
        dict(goal_type="between", goal_value=None, goal_min=Decimal(5), goal_max=Decimal(2)),  # min > max
    ],
)
def test_invalid_goal_shapes_are_rejected_by_the_database(world, goal):
    violates(world, make_measurable("bad", owner_id="u2", **goal))


# ---- rocks / milestones -------------------------------------------------------------------------

def test_rocks_are_listed_for_a_team_and_quarter_only(world):
    add(world, make_rock("r_cur", owner_id="u2"), make_rock("r_old", owner_id="u2", quarter="2026-Q3"),
        make_rock("r_other", team_id="t2", owner_id="u2"))
    repo = RockRepository(world)
    assert [r.id for r in repo.list_for_team("t1", "2026-Q4")] == ["r_cur"]
    assert [r.id for r in repo.list_for_team("t1", "2026-Q3")] == ["r_old"]
    assert repo.list_for_team("t1", "2027-Q1") == []


@pytest.mark.parametrize("quarter", ["2026-Q5", "2026-Q0", "26-Q1", "2026Q1", "2026-q1", "Q1-2026"])
def test_quarter_must_look_like_yyyy_qn(world, quarter):
    violates(world, make_rock("bad", owner_id="u2", quarter=quarter))


@pytest.mark.parametrize("status", ["on_track", "off_track", "complete"])
def test_rock_status_accepts_the_three_values(world, status):
    add(world, make_rock("ok", owner_id="u2", status=status))


@pytest.mark.parametrize("status", ["done", "Complete", "", "off-track"])
def test_rock_status_rejects_anything_else(world, status):
    violates(world, make_rock("bad", owner_id="u2", status=status))


def test_milestones_are_ordered_by_due_date_then_id_and_limited_to_the_given_rocks(world):
    add(world, make_rock("r1", owner_id="u2"), make_rock("r2", owner_id="u2"), make_rock("r3", owner_id="u2"))
    d = date(2026, 12, 1)
    add(world, make_milestone("z", "r1", due_date=d), make_milestone("a", "r1", due_date=d),
        make_milestone("early", "r1", due_date=d - timedelta(days=30)), make_milestone("other", "r2"),
        make_milestone("skipped", "r3"))
    got = MilestoneRepository(world).list_for_rocks(["r1", "r2"])
    assert [m.id for m in got if m.rock_id == "r1"] == ["early", "a", "z"]
    assert {m.rock_id for m in got} == {"r1", "r2"}


def test_milestones_for_no_rocks_is_empty(world):
    assert MilestoneRepository(world).list_for_rocks([]) == []


def test_a_milestone_needs_an_existing_rock(world):
    violates(world, make_milestone("m", "ghost"))
