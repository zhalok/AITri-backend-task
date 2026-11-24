"""Measurable status rule (brief 2.6): boundaries are on track; empty closed week off track; empty current week pending."""
from datetime import date
from decimal import Decimal as D

import pytest

from app.modules.measurable.rules import measurable_status
from tests.helpers import make_measurable

CLOSED, CURRENT = date(2026, 11, 2), date(2026, 11, 9)


def status(value, week=CLOSED, **goal):
    return measurable_status(make_measurable(**goal), None if value is None else D(str(value)), week, CURRENT)


@pytest.mark.parametrize("value,expected", [(9.99, "off_track"), (10, "on_track"), (10.01, "on_track")])
def test_at_least_boundary_is_on_track(value, expected):
    assert status(value, goal_type="at_least", goal_value=D(10)) == expected


@pytest.mark.parametrize("value,expected", [(9.99, "on_track"), (10, "on_track"), (10.01, "off_track")])
def test_at_most_boundary_is_on_track(value, expected):
    assert status(value, goal_type="at_most", goal_value=D(10)) == expected


@pytest.mark.parametrize("value,expected", [(9.99, "off_track"), (10, "on_track"), (10.01, "off_track")])
def test_exactly_only_matches_the_value(value, expected):
    assert status(value, goal_type="exactly", goal_value=D(10)) == expected


@pytest.mark.parametrize("value,expected", [
    (4.99, "off_track"), (5, "on_track"), (7, "on_track"), (10, "on_track"), (10.01, "off_track"),
])
def test_between_includes_both_ends(value, expected):
    assert status(value, goal_type="between", goal_value=None, goal_min=D(5), goal_max=D(10)) == expected


def test_zero_and_negative_scores_are_scores_not_missing():
    assert status(0, goal_type="at_most", goal_value=D(0)) == "on_track"
    assert status(-1, goal_type="at_least", goal_value=D(0)) == "off_track"


def test_closed_week_without_a_score_is_off_track():
    assert status(None, week=CLOSED, goal_type="at_most", goal_value=D(10)) == "off_track"


def test_current_week_without_a_score_is_pending():
    assert status(None, week=CURRENT, goal_type="at_least", goal_value=D(10)) == "pending"


def test_current_week_with_a_score_is_judged_against_the_goal():
    assert status(12, week=CURRENT, goal_type="at_least", goal_value=D(10)) == "on_track"
    assert status(8, week=CURRENT, goal_type="at_least", goal_value=D(10)) == "off_track"
