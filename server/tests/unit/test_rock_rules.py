"""Rock status and progress (brief 2.6), and round-half-up."""
from datetime import date

import pytest

from app.core.rounding import percent
from app.modules.rock.rules import rock_progress, rock_status
from tests.helpers import make_milestone

TODAY = date(2026, 11, 11)


@pytest.mark.parametrize("part,whole,expected", [(1, 8, 13), (1, 3, 33), (2, 3, 67), (1, 2, 50), (0, 5, 0), (5, 5, 100), (1, 16, 6), (3, 8, 38)])
def test_percent_rounds_half_up(part, whole, expected):
    assert percent(part, whole) == expected  # 1/8 = 12.5 -> 13, 3/8 = 37.5 -> 38, 1/16 = 6.25 -> 6


def test_complete_stays_complete_even_with_an_unfinished_past_due_milestone():
    assert rock_status("complete", [make_milestone(due_date=date(2026, 10, 1))], TODAY) == "complete"


def test_seeded_off_track_stays_off_track_with_no_late_milestone():
    assert rock_status("off_track", [make_milestone(due_date=date(2026, 12, 1))], TODAY) == "off_track"


def test_unfinished_milestone_past_due_makes_it_off_track():
    assert rock_status("on_track", [make_milestone(due_date=date(2026, 11, 10))], TODAY) == "off_track"


def test_milestone_due_today_is_not_past_due():
    assert rock_status("on_track", [make_milestone(due_date=TODAY)], TODAY) == "on_track"


def test_a_finished_past_due_milestone_does_not_count():
    assert rock_status("on_track", [make_milestone(due_date=date(2026, 10, 1), done=True)], TODAY) == "on_track"


def test_no_milestones_means_the_seeded_status_alone():
    assert rock_status("on_track", [], TODAY) == "on_track"
    assert rock_status("off_track", [], TODAY) == "off_track"


def test_progress_is_done_over_total_rounded_half_up():
    ms = [make_milestone(f"m{i}", done=i == 0) for i in range(8)]  # 1 of 8 = 12.5%
    assert rock_progress("on_track", ms) == 13


def test_progress_with_no_milestones_is_zero_or_100_once_complete():
    assert rock_progress("on_track", []) == 0
    assert rock_progress("off_track", []) == 0
    assert rock_progress("complete", []) == 100
