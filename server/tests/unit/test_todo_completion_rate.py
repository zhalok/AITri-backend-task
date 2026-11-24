"""To-Do completion rate (brief 2.6). Week under test: Mon 2026-11-02 .. Sun 2026-11-08, America/Chicago (UTC-6)."""
from datetime import date

import pytest

from app.modules.todo.rules import completion_rate
from tests.helpers import make_clock, make_todo, utc

WEEK = date(2026, 11, 2)
END = make_clock().week_end(WEEK)


def rate(todos):
    return completion_rate(todos, WEEK, END)


def due_in_week(n, done=0, day=date(2026, 11, 4)):
    return [make_todo(f"t{i}", due_date=day, done_at=utc("2026-11-05T12:00:00Z") if i < done else None) for i in range(n)]


def test_week_end_is_next_monday_midnight_company_time():
    assert END == utc("2026-11-09T06:00:00Z")  # Monday 00:00 CST


def test_zero_due_means_no_rate():
    r = rate([make_todo(due_date=date(2026, 11, 9)), make_todo("b", due_date=date(2026, 11, 1))])
    assert (r.due, r.rate, r.meets_target) == (0, None, None)


def test_exactly_ninety_percent_meets_the_target():
    r = rate(due_in_week(10, done=9))
    assert (r.rate, r.meets_target) == (90, True)


def test_just_below_ninety_misses_the_target():
    r = rate(due_in_week(10, done=8))
    assert (r.rate, r.meets_target) == (80, False)


def test_rounded_up_to_ninety_still_misses_when_the_exact_fraction_is_below():
    r = rate(due_in_week(200, done=179))  # 89.5% rounds to 90 but is not 90
    assert (r.rate, r.meets_target) == (90, False)


def test_rate_rounds_half_up():
    assert rate(due_in_week(8, done=1)).rate == 13  # 12.5%


def test_done_after_the_due_week_counts_as_not_done():
    late = make_todo(due_date=date(2026, 11, 4), done_at=utc("2026-11-09T06:00:00Z"))  # Monday 00:00 local
    assert rate([late]).done == 0


def test_done_in_the_last_second_of_the_week_counts():
    ok = make_todo(due_date=date(2026, 11, 4), done_at=utc("2026-11-09T05:59:59Z"))  # Sunday 23:59:59 local
    assert rate([ok]).done == 1


def test_done_early_counts():
    early = make_todo(due_date=date(2026, 11, 6), done_at=utc("2026-10-20T12:00:00Z"))
    assert rate([early]).done == 1


@pytest.mark.parametrize("due,counted", [(date(2026, 11, 1), 0), (date(2026, 11, 2), 1), (date(2026, 11, 8), 1), (date(2026, 11, 9), 0)])
def test_due_date_week_boundaries(due, counted):
    assert rate([make_todo(due_date=due)]).due == counted
