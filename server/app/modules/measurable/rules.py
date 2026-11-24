"""Measurable status (brief 2.6): compare a week's score with the goal.

Pure functions, no database: the one place this rule lives, used by the Scorecard, Make it an Issue and
the meeting summary.
"""
from datetime import date
from decimal import Decimal

ON_TRACK = "on_track"
OFF_TRACK = "off_track"
PENDING = "pending"


def meets_goal(goal_type: str, value: Decimal, goal_value, goal_min, goal_max) -> bool:
    """Boundaries count as meeting the goal."""
    if goal_type == "at_least":
        return value >= goal_value
    if goal_type == "at_most":
        return value <= goal_value
    if goal_type == "exactly":
        return value == goal_value
    if goal_type == "between":
        return goal_min <= value <= goal_max
    raise ValueError(f"unknown goal type {goal_type!r}")


def measurable_status(measurable, value: Decimal | None, week_start: date, current_week_start: date) -> str:
    """A scored week is on or off track. An empty closed week is off track; an empty current week is pending."""
    if value is None:
        return OFF_TRACK if week_start < current_week_start else PENDING
    ok = meets_goal(measurable.goal_type, value, measurable.goal_value, measurable.goal_min, measurable.goal_max)
    return ON_TRACK if ok else OFF_TRACK
