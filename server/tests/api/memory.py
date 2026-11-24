"""An in-memory database for API tests: the real app, the real use cases and services, no Postgres.

The data is the real seed.json, loaded by the app's own `load_seed` into a `Store` instead of a session. Each
repository below implements the same methods as its SQL twin over plain lists of real model objects, so a request
travels HTTP -> controller -> use case (RBAC, team scope) -> service -> repository exactly as in production.
What this cannot prove is database behaviour (unique indexes, row locks, ON CONFLICT): those have their own tests
against real Postgres.
"""
import json
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from app.core.errors import ConflictError
from app.modules.issue.models import Issue
from app.modules.meeting.models import MeetingAttendee, MeetingRating, MeetingSection, MeetingStatus
from app.modules.score.models import Score
from app.seed import DEFAULT_SEED, load_seed


class Store:
    """Everything the seed loads, grouped by entity type."""

    def __init__(self):
        self.by_type: dict[str, list] = defaultdict(list)

    def merge(self, entity):  # load_seed calls session.merge(...) then session.flush()
        self.by_type[type(entity).__name__].append(entity)
        return entity

    def flush(self):
        pass

    def all(self, name: str) -> list:
        return self.by_type[name]


def seeded_store() -> Store:
    store = Store()
    load_seed(store, json.loads(DEFAULT_SEED.read_text()))  # type: ignore[arg-type]
    return store


class FakeSession:
    """Stands in for the SQLAlchemy session: nothing here talks to a database."""

    def execute(self, *_a, **_k):
        return None


class Repo:
    def __init__(self, store: Store, name: str):
        self.items = store.all(name)

    def get(self, id_):
        return next((i for i in self.items if i.id == id_), None)

    def add(self, entity):
        self.items.append(entity)
        return entity

    def save(self):
        pass


class UserRepo(Repo):
    def __init__(self, store):
        super().__init__(store, "User")

    def list_all(self):
        return sorted(self.items, key=lambda u: u.id)

    def get_many(self, ids):
        return [u for u in self.items if u.id in ids]

    def get_by_email(self, email):
        return next((u for u in self.items if u.email.lower() == email.lower()), None)


class TeamRepo(Repo):
    def __init__(self, store):
        super().__init__(store, "Team")
        self.users = store.all("User")
        self.memberships = {(m.user_id, m.team_id) for m in store.all("Membership")}

    def list_all(self):
        return sorted(self.items, key=lambda t: t.name)

    def list_for_user(self, user_id):
        return sorted((t for t in self.items if (user_id, t.id) in self.memberships), key=lambda t: t.name)

    def is_member(self, user_id, team_id):
        return (user_id, team_id) in self.memberships

    def list_members_of_teams(self, team_ids):
        ids = {u for (u, t) in self.memberships if t in team_ids}
        return sorted((u for u in self.users if u.id in ids), key=lambda u: (u.name, u.id))

    def list_members(self, team_id):
        return sorted((u for u in self.users if (u.id, team_id) in self.memberships), key=lambda u: u.name)


class MeasurableRepo(Repo):
    def __init__(self, store):
        super().__init__(store, "Measurable")

    def list_for_team(self, team_id):
        return sorted((m for m in self.items if m.team_id == team_id), key=lambda m: m.id)


class ScoreRepo:
    def __init__(self, store):
        self.items = store.all("Score")

    def _find(self, measurable_id, week_start):
        return next((s for s in self.items if s.measurable_id == measurable_id and s.week_start == week_start), None)

    def list_for(self, measurable_ids, weeks):
        return [s for s in self.items if s.measurable_id in measurable_ids and s.week_start in weeks]

    def upsert(self, measurable_id, week_start, value):
        row = self._find(measurable_id, week_start)
        if row is None:
            row = Score(measurable_id=measurable_id, week_start=week_start, value=value)
            self.items.append(row)
        row.value = value
        return row

    def set_if_seen(self, measurable_id, week_start, value, seen):
        row = self._find(measurable_id, week_start)
        if (None if row is None else row.value) != seen:
            return None
        return self.upsert(measurable_id, week_start, value)


class IssueRepo(Repo):
    def __init__(self, store):
        super().__init__(store, "Issue")

    def list_unsolved(self, team_id):
        rows = [i for i in self.items if i.team_id == team_id and i.solved_at is None]
        return sorted(rows, key=lambda i: (-(i.priority or 0), i.created_at, i.id))  # priority 5 first, none last

    def list_solved(self, team_id):
        rows = [i for i in self.items if i.team_id == team_id and i.solved_at is not None]
        return sorted(rows, key=lambda i: i.id)  # then newest solve first

    def list_solved_in_meeting(self, meeting_id):
        return sorted((i for i in self.items if i.solved_in_meeting_id == meeting_id), key=lambda i: (i.solved_at, i.id))

    def get_for_update(self, issue_id):
        return self.get(issue_id)

    def find_unsolved_by_source(self, measurable_id, week_start: date):
        return next((i for i in self.items if i.source_measurable_id == measurable_id
                     and i.source_week_start == week_start and i.solved_at is None), None)

    def insert_from_source_if_absent(self, values):
        if self.find_unsolved_by_source(values["source_measurable_id"], values["source_week_start"]):
            return False
        self.items.append(Issue(**values))
        return True


class TodoRepo(Repo):
    def __init__(self, store):
        super().__init__(store, "Todo")

    def list_for_team(self, team_id):
        return sorted((t for t in self.items if t.team_id == team_id), key=lambda t: (t.due_date, t.id))

    def list_created_in_meeting(self, meeting_id):
        return sorted((t for t in self.items if t.created_in_meeting_id == meeting_id), key=lambda t: (t.created_at, t.id))


class RockRepo(Repo):
    def __init__(self, store):
        super().__init__(store, "Rock")

    def list_for_team(self, team_id, quarter):
        return sorted((r for r in self.items if r.team_id == team_id and r.quarter == quarter), key=lambda r: r.id)


class MilestoneRepo(Repo):
    def __init__(self, store):
        super().__init__(store, "Milestone")

    def list_for_rocks(self, rock_ids):
        return sorted((m for m in self.items if m.rock_id in rock_ids), key=lambda m: (m.due_date, m.id))


class MeetingRepo(Repo):
    def __init__(self, store):
        super().__init__(store, "Meeting")
        self.attendees = store.all("MeetingAttendee")
        self.rating_rows = store.all("MeetingRating")
        self.section_rows: list[MeetingSection] = []

    def add_meeting(self, meeting):
        if self.get_active_for_team(meeting.team_id):
            raise ConflictError("This team already has an active meeting")
        meeting.status = meeting.status or MeetingStatus.ACTIVE  # the column default applies on INSERT only
        return self.add(meeting)

    def list_ended_for_team(self, team_id):
        return sorted((m for m in self.items if m.team_id == team_id and m.status == MeetingStatus.ENDED), key=lambda m: m.id)

    def get_active_for_team(self, team_id):
        return next((m for m in self.items if m.team_id == team_id and m.status == MeetingStatus.ACTIVE), None)

    def add_attendee(self, meeting_id, user_id):
        if user_id not in self.attendee_ids(meeting_id):
            self.attendees.append(MeetingAttendee(meeting_id=meeting_id, user_id=user_id))

    def remove_attendee(self, meeting_id, user_id):
        self.rating_rows[:] = [r for r in self.rating_rows if not (r.meeting_id == meeting_id and r.user_id == user_id)]
        self.attendees[:] = [a for a in self.attendees if not (a.meeting_id == meeting_id and a.user_id == user_id)]

    def attendee_ids(self, meeting_id):
        return sorted(a.user_id for a in self.attendees if a.meeting_id == meeting_id)

    def upsert_rating(self, meeting_id, user_id, rating):
        row = next((r for r in self.rating_rows if r.meeting_id == meeting_id and r.user_id == user_id), None)
        if row is None:
            self.rating_rows.append(MeetingRating(meeting_id=meeting_id, user_id=user_id, rating=rating))
        else:
            row.rating = rating

    def ratings(self, meeting_id):
        return {r.user_id: r.rating for r in self.rating_rows if r.meeting_id == meeting_id}

    def open_section(self, meeting_id, section, at: datetime):
        self.section_rows.append(MeetingSection(meeting_id=meeting_id, section=section, started_at=at))

    def close_open_section(self, meeting_id, at: datetime):
        for row in self.section_rows:
            if row.meeting_id == meeting_id and row.ended_at is None:
                row.ended_at = at

    def sections(self, meeting_id):
        return sorted((s for s in self.section_rows if s.meeting_id == meeting_id), key=lambda s: s.started_at)


class AuditRepo:
    def list_events(self, **_filters):
        return []
