"""Load seed.json into the database. Safe to rerun: every row is upserted by its primary key, so
running it twice changes nothing, and ids from the file (u1, m1, t12, ...) are kept.

    python -m app.seed [path/to/seed.json]     (or set SEED_FILE)

The file has no passwords (sign-in is by email) and no company table (the company time zone comes
from COMPANY_TIMEZONE), so those parts are not loaded.

Meeting links: the file does not say which meeting an Issue was solved in or a To-Do created in.
They are derived from time: inside a team's meeting window (started_at..ended_at, inclusive).
"""
import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

import app.models  # noqa: F401  (registers every table)
from app.core.database import SessionLocal, tag_actor
from app.modules.issue.models import Issue
from app.modules.measurable.models import Measurable
from app.modules.meeting.models import Meeting, MeetingAttendee, MeetingRating, MeetingStatus, Section
from app.modules.milestone.models import Milestone
from app.modules.rock.models import Rock
from app.modules.score.models import Score
from app.modules.team.models import Membership, Team
from app.modules.todo.models import Todo
from app.modules.user.models import User

DEFAULT_SEED = Path(__file__).resolve().parents[2] / "seed.json"


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _dec(value) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _meeting_at(meetings: list[dict], team_id: str, instant: datetime | None) -> str | None:
    if instant is None:
        return None
    for m in meetings:
        if m["team_id"] == team_id and _dt(m["started_at"]) <= instant <= _dt(m["ended_at"]):
            return m["id"]
    return None


def load_seed(session: Session, data: dict) -> dict[str, int]:
    """Upsert everything in foreign-key order. Returns row counts per table. Does not commit."""

    def put(entity):
        session.merge(entity)
        session.flush()

    for t in data["teams"]:
        put(Team(id=t["id"], name=t["name"]))
    for u in data["users"]:
        put(User(id=u["id"], name=u["name"], email=u["email"], role=u["role"]))
    for m in data["memberships"]:
        put(Membership(user_id=m["user_id"], team_id=m["team_id"]))

    for m in data["measurables"]:
        g = m["goal"]
        between = g["type"] == "between"
        put(Measurable(
            id=m["id"], team_id=m["team_id"], owner_id=m["owner_id"], name=m["name"], unit=m["unit"],
            goal_type=g["type"], goal_value=None if between else _dec(g["value"]),
            goal_min=_dec(g["min"]) if between else None, goal_max=_dec(g["max"]) if between else None,
        ))
    for s in data["scores"]:
        put(Score(measurable_id=s["measurable_id"], week_start=date.fromisoformat(s["week_start"]), value=_dec(s["value"])))

    for r in data["rocks"]:
        put(Rock(id=r["id"], team_id=r["team_id"], owner_id=r["owner_id"], title=r["title"],
                 quarter=r["quarter"], status=r["status"]))
    for ms in data["milestones"]:
        put(Milestone(id=ms["id"], rock_id=ms["rock_id"], title=ms["title"],
                      due_date=date.fromisoformat(ms["due_date"]), done=ms["done"]))

    meetings = data["meetings"]
    for m in meetings:
        put(Meeting(
            id=m["id"], team_id=m["team_id"], facilitator_id=m["facilitator_id"], started_at=_dt(m["started_at"]),
            ended_at=_dt(m["ended_at"]), current_section=Section.CONCLUDE, section_started_at=_dt(m["ended_at"]),
            status=MeetingStatus.ENDED,
        ))
        for user_id in m["attendee_ids"]:
            put(MeetingAttendee(meeting_id=m["id"], user_id=user_id))
        for r in m["ratings"]:
            put(MeetingRating(meeting_id=m["id"], user_id=r["user_id"], rating=r["rating"]))

    for i in data["issues"]:
        src = i.get("source")
        solved_at = _dt(i["solved_at"])
        put(Issue(
            id=i["id"], team_id=i["team_id"], owner_id=i["owner_id"], title=i["title"], priority=i["priority"],
            created_at=_dt(i["created_at"]), solved_at=solved_at, resolution_note=i["resolution_note"],
            source_measurable_id=src["measurable_id"] if src else None,
            source_week_start=date.fromisoformat(src["week_start"]) if src else None,
            solved_in_meeting_id=_meeting_at(meetings, i["team_id"], solved_at),
        ))
    for t in data["todos"]:
        created_at = _dt(t["created_at"])
        put(Todo(
            id=t["id"], team_id=t["team_id"], owner_id=t["owner_id"], title=t["title"],
            due_date=date.fromisoformat(t["due_date"]), done_at=_dt(t["done_at"]), created_at=created_at,
            source_issue_id=t["source_issue_id"], created_in_meeting_id=_meeting_at(meetings, t["team_id"], created_at),
        ))

    return {k: len(data[k]) for k in (
        "teams", "users", "memberships", "measurables", "scores", "rocks", "milestones", "meetings", "issues", "todos")}


def main(path: Path | None = None) -> None:
    # Precedence: explicit argument, then command line, then SEED_FILE (used in Docker), then the repo's seed.json.
    path = path or (Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ.get("SEED_FILE", DEFAULT_SEED)))
    data = json.loads(path.read_text())
    with SessionLocal() as session:
        tag_actor(session, "seed")  # the audit trail shows the seed as the author of what it loaded
        counts = load_seed(session, data)
        session.commit()
    print("Seeded:", ", ".join(f"{n} {k}" for k, n in counts.items()))


if __name__ == "__main__":
    main()
