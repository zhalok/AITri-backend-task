"""To-Do completion rate (brief 2.6): done by the end of the week / due that week. Target 90%."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.core.rounding import percent

TARGET_PERCENT = 90


@dataclass
class CompletionRate:
    week_start: date
    due: int
    done: int
    rate: int | None  # whole percent, None when nothing was due
    meets_target: bool | None


def completion_rate(todos, week_start: date, week_end: datetime) -> CompletionRate:
    """`week_end` is the first instant after the week (next Monday 00:00 company time).

    Due that week: due date Monday..Sunday. Done by the end of it: done_at before `week_end`; marking it done
    afterwards counts as not done. The 90% target is tested on the exact fraction, not the rounded percent.
    """
    due = [t for t in todos if week_start <= t.due_date <= week_start + timedelta(days=6)]
    if not due:
        return CompletionRate(week_start, 0, 0, None, None)
    done = sum(1 for t in due if t.done_at is not None and t.done_at < week_end)
    return CompletionRate(week_start, len(due), done, percent(done, len(due)), done * 100 >= TARGET_PERCENT * len(due))
