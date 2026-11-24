"""Attendance follows the connection: a meeting page's socket joins the meeting, its last close leaves it.

Only sockets on the meeting endpoint (`/ws/teams/{id}/meeting`, the Meeting page) count. The Team page
uses a different endpoint (`/ws/teams/{id}/sync`) that never changes who is in the meeting. A user may have the meeting open in several tabs, so
they leave only when the last of their presence sockets closes.

A refresh, a sleeping laptop or a dropped connection are disconnects like any other: the user leaves, and
their next connection joins again. Ratings leave with them. The facilitator is never removed (nobody could
run the meeting); an ended meeting is never changed, so its attendee list stays as it was at the end.

The open-socket counts live in this process. With several API workers they would need to move to Redis.
"""
import logging
from collections import Counter

from app.core.clock import Clock
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.errors import AppError
from app.modules.meeting.repository import MeetingRepository
from app.modules.meeting.service import MeetingService
from app.modules.user.models import User

log = logging.getLogger("realtime")

_open: Counter[tuple[str, str]] = Counter()  # (team_id, user_id) -> open presence sockets


def opened(user: User, team_id: str) -> None:
    _open[(team_id, user.id)] += 1


def closed(user: User, team_id: str) -> bool:
    """Count one presence socket closing. True when it was the user's last one in this team."""
    key = (team_id, user.id)
    _open[key] -= 1
    if _open[key] > 0:
        return False
    del _open[key]
    return True


def _with_active_meeting(team_id: str, action) -> None:
    """Run `action(service, meeting)` on the team's running meeting, if any. Never raises."""
    try:
        settings = get_settings()
        with SessionLocal() as session:
            service = MeetingService(MeetingRepository(session), Clock(settings.app_now, settings.company_timezone))
            meeting = service.get_active_for_team(team_id)
            if meeting is not None:
                action(service, meeting)
                session.commit()  # the NOTIFY trigger tells everyone else once this commits
    except AppError as exc:  # e.g. the facilitator "left", or the meeting just ended: nothing changes
        log.info("presence change ignored: %s", exc.message)
    except Exception:
        log.exception("could not update meeting attendance")


def join_active_meeting(user: User, team_id: str) -> None:
    _with_active_meeting(team_id, lambda service, meeting: service.join(meeting, user))


def leave_active_meeting(user: User, team_id: str) -> None:
    _with_active_meeting(team_id, lambda service, meeting: service.leave(meeting, user))
