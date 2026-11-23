"""In-memory stand-ins for repositories, so service tests need no database."""
from datetime import date

from app.core.errors import ConflictError
from app.modules.issue.models import Issue


class FakeRepo:
    def __init__(self, items=None):
        self.items = list(items or [])
        self.saves = 0

    def get(self, id_):
        return next((i for i in self.items if i.id == id_), None)

    def add(self, entity):
        self.items.append(entity)
        return entity

    def save(self):
        self.saves += 1


class FakeIssueRepo(FakeRepo):
    def list_unsolved(self, team_id):
        return [i for i in self.items if i.team_id == team_id and i.solved_at is None]

    def list_solved(self, team_id):
        return [i for i in self.items if i.team_id == team_id and i.solved_at is not None]

    def find_unsolved_by_source(self, measurable_id, week_start: date):
        return next((i for i in self.items if i.source_measurable_id == measurable_id
                     and i.source_week_start == week_start and i.solved_at is None), None)

    def insert_from_source_if_absent(self, values):
        if self.find_unsolved_by_source(values["source_measurable_id"], values["source_week_start"]):
            return False
        self.items.append(Issue(**values))
        return True


class FakeTodoRepo(FakeRepo):
    def list_for_team(self, team_id):
        return [t for t in self.items if t.team_id == team_id]


class FakeMeetingRepo(FakeRepo):
    def __init__(self):
        super().__init__()
        self.attendees: dict[str, set[str]] = {}
        self.rating_rows: dict[str, dict[str, int]] = {}

    def add_meeting(self, meeting):
        if any(m.team_id == meeting.team_id and m.ended_at is None for m in self.items):
            raise ConflictError("This team already has an active meeting")
        return self.add(meeting)

    def get_active_for_team(self, team_id):
        return next((m for m in self.items if m.team_id == team_id and m.ended_at is None), None)

    def add_attendee(self, meeting_id, user_id):
        self.attendees.setdefault(meeting_id, set()).add(user_id)

    def attendee_ids(self, meeting_id):
        return sorted(self.attendees.get(meeting_id, set()))

    def upsert_rating(self, meeting_id, user_id, rating):
        self.rating_rows.setdefault(meeting_id, {})[user_id] = rating

    def ratings(self, meeting_id):
        return dict(self.rating_rows.get(meeting_id, {}))


class FakeScoreRepo(FakeRepo):
    def __init__(self, scores=None):
        super().__init__()
        self.scores = scores or []  # Score-like objects
        self.upserts: list[tuple] = []

    def list_for(self, measurable_ids, weeks):
        return [s for s in self.scores if s.measurable_id in measurable_ids and s.week_start in weeks]

    def upsert(self, measurable_id, week_start, value):
        self.upserts.append((measurable_id, week_start, value))
        return ("saved", measurable_id, week_start, value)


class FakeRockRepo(FakeRepo):
    def __init__(self, items=None):
        super().__init__(items)
        self.asked: list[tuple] = []

    def list_for_team(self, team_id, quarter):
        self.asked.append((team_id, quarter))
        return [r for r in self.items if r.team_id == team_id and r.quarter == quarter]


class FakeMilestoneRepo(FakeRepo):
    def list_for_rocks(self, rock_ids):
        return sorted((m for m in self.items if m.rock_id in rock_ids), key=lambda m: (m.due_date, m.id))


class FakeUserRepo(FakeRepo):
    def list_all(self):
        return sorted(self.items, key=lambda u: u.id)

    def get_many(self, ids):
        return [u for u in self.items if u.id in ids]

    def get_by_email(self, email):
        return next((u for u in self.items if u.email.lower() == email.lower()), None)


class FakeTeamRepo(FakeRepo):
    def __init__(self, teams=None, users=None, memberships=None):
        super().__init__(teams)
        self.users = list(users or [])
        self.memberships = set(memberships or [])  # (user_id, team_id)

    def list_all(self):
        return sorted(self.items, key=lambda t: t.name)

    def list_for_user(self, user_id):
        return sorted((t for t in self.items if (user_id, t.id) in self.memberships), key=lambda t: t.name)

    def is_member(self, user_id, team_id):
        return (user_id, team_id) in self.memberships

    def list_members(self, team_id):
        return sorted((u for u in self.users if (u.id, team_id) in self.memberships), key=lambda u: u.name)

    def list_members_of_teams(self, team_ids):
        return sorted((u for u in self.users if any((u.id, t) in self.memberships for t in team_ids)),
                      key=lambda u: (u.name, u.id))
