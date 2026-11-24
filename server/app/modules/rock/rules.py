"""Rock status and progress (brief 2.6). Pure functions over the seeded status and the Milestones."""
from datetime import date

from app.core.rounding import percent

COMPLETE = "complete"
OFF_TRACK = "off_track"
ON_TRACK = "on_track"


def rock_status(seeded_status: str, milestones, today: date) -> str:
    """Complete stays complete; off-track stays off-track; an unfinished Milestone past due makes it off-track.

    A Milestone due today is not past due. With no Milestones the seeded status stands alone.
    """
    if seeded_status in (COMPLETE, OFF_TRACK):
        return seeded_status
    if any(not m.done and m.due_date < today for m in milestones):
        return OFF_TRACK
    return ON_TRACK


def rock_progress(seeded_status: str, milestones) -> int:
    """Done Milestones / all Milestones as a whole percent. No Milestones: 0, or 100 once Complete."""
    if not milestones:
        return 100 if seeded_status == COMPLETE else 0
    return percent(sum(1 for m in milestones if m.done), len(milestones))
