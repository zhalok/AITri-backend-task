from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.errors import DomainValidationError
from app.modules.milestone.service import MilestoneService
from app.modules.rock.service import RockService
from app.modules.score.service import ScoreService
from tests.fakes import FakeMilestoneRepo, FakeRockRepo, FakeScoreRepo
from tests.helpers import make_clock, make_milestone, make_rock


def score(m, w, v):
    return SimpleNamespace(measurable_id=m, week_start=w, value=Decimal(v))


# ---- scores -----------------------------------------------------------------------------------

def test_set_score_delegates_to_an_upsert(clock):
    repo = FakeScoreRepo()
    ScoreService(repo, clock).set_score("m1", date(2026, 11, 2), Decimal("12.5"))
    assert repo.upserts == [("m1", date(2026, 11, 2), Decimal("12.5"))]


@pytest.mark.parametrize("week", [date(2026, 11, 3), date(2026, 11, 1), date(2026, 11, 8)])
def test_set_score_requires_a_monday(clock, week):
    repo = FakeScoreRepo()
    with pytest.raises(DomainValidationError):
        ScoreService(repo, clock).set_score("m1", week, Decimal(1))
    assert repo.upserts == []


@pytest.mark.parametrize("week", [date(2026, 8, 10), date(2026, 11, 16)])
def test_set_score_rejects_weeks_outside_the_13_week_window(clock, week):
    with pytest.raises(DomainValidationError):
        ScoreService(FakeScoreRepo(), clock).set_score("m1", week, Decimal(1))


@pytest.mark.parametrize("week", [date(2026, 8, 17), date(2026, 11, 9)])
def test_set_score_accepts_the_oldest_and_the_current_week(clock, week):
    repo = FakeScoreRepo()
    ScoreService(repo, clock).set_score("m1", week, Decimal(1))
    assert len(repo.upserts) == 1


def test_scores_by_measurable_groups_and_keeps_missing_measurables_empty(clock):
    w1, w2 = date(2026, 11, 2), date(2026, 11, 9)
    repo = FakeScoreRepo([score("m1", w1, "5"), score("m1", w2, "6"), score("m2", w1, "7"), score("other", w1, "9")])
    grouped = ScoreService(repo, clock).scores_by_measurable(["m1", "m2", "m3"], [w1, w2])
    assert grouped == {"m1": {w1: Decimal(5), w2: Decimal(6)}, "m2": {w1: Decimal(7)}, "m3": {}}


def test_scores_by_measurable_with_no_measurables(clock):
    assert ScoreService(FakeScoreRepo(), clock).scores_by_measurable([], []) == {}


# ---- rocks ------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "now,quarter",
    [
        ("2026-11-11T15:00:00Z", "2026-Q4"),
        ("2026-01-01T06:00:00Z", "2026-Q1"),   # Jan 1 00:00 Chicago
        ("2026-04-01T04:59:59Z", "2026-Q1"),   # Mar 31 23:59:59 CDT
        ("2026-04-01T05:00:00Z", "2026-Q2"),   # Apr 1 00:00 CDT
        ("2026-10-01T04:59:59Z", "2026-Q3"),
        ("2026-10-01T05:00:00Z", "2026-Q4"),
        ("2027-01-01T05:59:59Z", "2026-Q4"),   # Dec 31 23:59:59 CST, still last year in Chicago
        ("2027-01-01T06:00:00Z", "2027-Q1"),
    ],
)
def test_current_quarter_is_a_calendar_quarter_in_company_time(now, quarter):
    assert RockService(FakeRockRepo(), make_clock(now)).current_quarter() == quarter


def test_list_current_asks_for_this_quarters_rocks_only(clock):
    repo = FakeRockRepo([make_rock("r1", quarter="2026-Q4"), make_rock("r2", quarter="2026-Q3"), make_rock("r3", team_id="t2")])
    rocks = RockService(repo, clock).list_current("t1")
    assert [r.id for r in rocks] == ["r1"]
    assert repo.asked == [("t1", "2026-Q4")]


# ---- milestones -------------------------------------------------------------------------------

def test_grouped_by_rock_orders_by_due_date_and_omits_rocks_without_milestones():
    repo = FakeMilestoneRepo([
        make_milestone("b", "r1", due_date=date(2026, 12, 1)),
        make_milestone("a", "r1", due_date=date(2026, 10, 1)),
        make_milestone("c", "r2", due_date=date(2026, 11, 1)),
    ])
    grouped = MilestoneService(repo).grouped_by_rock(["r1", "r2", "r3"])
    assert [m.id for m in grouped["r1"]] == ["a", "b"] and [m.id for m in grouped["r2"]] == ["c"]
    assert "r3" not in grouped


def test_grouped_by_rock_with_no_rocks():
    assert MilestoneService(FakeMilestoneRepo()).grouped_by_rock([]) == {}
