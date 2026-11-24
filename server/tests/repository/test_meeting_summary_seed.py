"""The summary of the two seeded meetings, checked against values worked out by hand from seed.json."""
import json
from datetime import datetime

import pytest

from app.core.rbac import Rbac
from app.modules.issue.repository import IssueRepository
from app.modules.issue.service import IssueService
from app.modules.measurable.repository import MeasurableRepository
from app.modules.measurable.service import MeasurableService
from app.modules.meeting.repository import MeetingRepository
from app.modules.meeting.service import MeetingService
from app.modules.meeting_summary.usecase import MeetingSummaryUseCase
from app.modules.score.repository import ScoreRepository
from app.modules.score.service import ScoreService
from app.modules.team.scope import TeamScope
from app.modules.todo.repository import TodoRepository
from app.modules.todo.service import TodoService
from app.modules.user.models import User
from app.modules.user.repository import UserRepository
from app.modules.user.service import UserService
from app.seed import DEFAULT_SEED, load_seed
from tests.helpers import make_clock

DATA = json.loads(DEFAULT_SEED.read_text())
ADMIN = User(id="admin", name="Admin", email="a@t.test", role="admin")


@pytest.fixture
def summaries(session):
    load_seed(session, DATA)
    clock = make_clock("2026-11-11T15:00:00Z")
    scores = ScoreService(ScoreRepository(session), clock)
    uc = MeetingSummaryUseCase(
        MeetingService(MeetingRepository(session), clock), IssueService(IssueRepository(session), clock),
        TodoService(TodoRepository(session), clock), MeasurableService(MeasurableRepository(session)), scores,
        UserService(UserRepository(session)), Rbac(), None, clock,  # the wide (admin) path needs no TeamScope
    )
    return lambda meeting_id: uc.admin_get(ADMIN, meeting_id)


def statuses(summary):
    return {m.measurable_id: m.status for m in summary.measurables}


def window(meeting_id):
    m = next(x for x in DATA["meetings"] if x["id"] == meeting_id)
    return m["team_id"], datetime.fromisoformat(m["started_at"].replace("Z", "+00:00")), \
        datetime.fromisoformat(m["ended_at"].replace("Z", "+00:00"))


def inside(meeting_id, stamp):
    _, start, end = window(meeting_id)
    return start <= datetime.fromisoformat(stamp.replace("Z", "+00:00")) <= end


def test_first_seeded_meeting_judges_the_week_of_oct_19(summaries):
    s = summaries("mt1")
    assert str(s.week_start) == "2026-10-19"
    # m1 12 >= 10, m2 2.4 <= 3, m3 2.0 is the lower edge of 2..4, m4 1 == 1, m5 has no score in a closed week
    assert statuses(s) == {"m1": "on_track", "m2": "on_track", "m3": "on_track", "m4": "on_track", "m5": "off_track"}
    assert s.measurables[4].score is None


def test_second_seeded_meeting_judges_the_week_of_oct_26(summaries):
    s = summaries("mt2")
    assert str(s.week_start) == "2026-10-26"
    # m1 9 < 10, m2 2.6 <= 3, m3 3.3 within 2..4, m4 0 != 1, m5 525 >= 500
    assert statuses(s) == {"m1": "off_track", "m2": "on_track", "m3": "on_track", "m4": "off_track", "m5": "on_track"}


@pytest.mark.parametrize("meeting_id,average", [("mt1", 8.0), ("mt2", 8.3)])
def test_rating_is_the_average_of_the_ratings_rounded_half_up(summaries, meeting_id, average):
    s = summaries(meeting_id)  # mt1: 8,9,7 -> 8.0   mt2: 8,9,8,8 -> 33/4 = 8.25 -> 8.3
    assert (s.rating.average, s.rating.count) == (average, len(s.rating.by_user))


@pytest.mark.parametrize("meeting_id", ["mt1", "mt2"])
def test_attendees_issues_and_todos_come_from_the_meeting(summaries, meeting_id):
    s = summaries(meeting_id)
    meeting = next(x for x in DATA["meetings"] if x["id"] == meeting_id)
    team = meeting["team_id"]
    assert sorted(a.id for a in s.attendees) == sorted(meeting["attendee_ids"])
    assert sorted(i.id for i in s.issues_solved) == sorted(
        i["id"] for i in DATA["issues"] if i["team_id"] == team and i["solved_at"] and inside(meeting_id, i["solved_at"]))
    assert sorted(t.id for t in s.todos_created) == sorted(
        t["id"] for t in DATA["todos"] if t["team_id"] == team and inside(meeting_id, t["created_at"]))


def test_a_running_meeting_has_no_summary_yet(session, summaries):
    from app.core.errors import ConflictError
    from app.modules.meeting.repository import MeetingRepository

    clock = make_clock("2026-11-11T15:00:00Z")
    started = MeetingService(MeetingRepository(session), clock).start("team_lead", session.get(User, "u2"))
    with pytest.raises(ConflictError):
        summaries(started.id)
