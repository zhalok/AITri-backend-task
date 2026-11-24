"""Builders for transient (not yet persisted) entities, and a Clock at any instant."""
from datetime import date, datetime, timezone
from decimal import Decimal

from app.core.clock import Clock
from app.modules.issue.models import Issue
from app.modules.measurable.models import Measurable
from app.modules.meeting.models import Meeting
from app.modules.milestone.models import Milestone
from app.modules.rock.models import Rock
from app.modules.team.models import Team
from app.modules.todo.models import Todo
from app.modules.user.models import User

NOW = datetime(2026, 11, 11, 15, 0, tzinfo=timezone.utc)  # Wed 2026-11-11 09:00 in Chicago
TZ = "America/Chicago"


def utc(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def make_clock(now: datetime | str = NOW) -> Clock:
    return Clock(utc(now) if isinstance(now, str) else now, TZ)


def make_user(id="u2", role="team_member", email=None, name=None) -> User:
    return User(id=id, name=name or f"User {id}", email=email or f"{id}@t.test", role=role)


def make_team(id="t1", name=None) -> Team:
    return Team(id=id, name=name or f"Team {id}")


def make_issue(id="i1", team_id="t1", owner_id="u2", title="Issue", priority=None, created_at=NOW, **kw) -> Issue:
    return Issue(id=id, team_id=team_id, owner_id=owner_id, title=title, priority=priority, created_at=created_at, **kw)


def make_todo(id="td1", team_id="t1", owner_id="u2", title="Todo", due_date=date(2026, 11, 18), done_at=None,
              created_at=NOW, source_issue_id=None, created_in_meeting_id=None) -> Todo:
    return Todo(id=id, team_id=team_id, owner_id=owner_id, title=title, due_date=due_date, done_at=done_at,
                created_at=created_at, source_issue_id=source_issue_id, created_in_meeting_id=created_in_meeting_id)


def make_measurable(id="m1", team_id="t1", owner_id="u2", name="Deals", unit="count", goal_type="at_least",
                    goal_value=Decimal(10), goal_min=None, goal_max=None) -> Measurable:
    return Measurable(id=id, team_id=team_id, owner_id=owner_id, name=name, unit=unit, goal_type=goal_type,
                      goal_value=goal_value, goal_min=goal_min, goal_max=goal_max)


def make_rock(id="r1", team_id="t1", owner_id="u2", title="Rock", quarter="2026-Q4", status="on_track") -> Rock:
    return Rock(id=id, team_id=team_id, owner_id=owner_id, title=title, quarter=quarter, status=status)


def make_milestone(id="ms1", rock_id="r1", title="Milestone", due_date=date(2026, 12, 1), done=False) -> Milestone:
    return Milestone(id=id, rock_id=rock_id, title=title, due_date=due_date, done=done)


def make_meeting(id="mt1", team_id="t1", facilitator_id="u2", started_at=NOW, ended_at=None,
                 current_section="scorecard", section_started_at=NOW) -> Meeting:
    return Meeting(id=id, team_id=team_id, facilitator_id=facilitator_id, started_at=started_at, ended_at=ended_at,
                   status="ended" if ended_at else "active",
                   current_section=current_section, section_started_at=section_started_at)
