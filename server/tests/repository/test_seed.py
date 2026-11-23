import json

import pytest
from sqlalchemy import func, select

from app.modules.issue.models import Issue
from app.modules.meeting.models import MeetingRating
from app.modules.score.models import Score
from app.modules.todo.models import Todo
from app.seed import DEFAULT_SEED, load_seed

DATA = json.loads(DEFAULT_SEED.read_text())


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_the_real_seed_file_loads_with_the_expected_counts(session):
    counts = load_seed(session, DATA)
    assert counts == {"teams": 3, "users": 9, "memberships": 11, "measurables": 7, "scores": 83, "rocks": 7,
                      "milestones": 12, "meetings": 2, "issues": 9, "todos": 20}
    assert count(session, Score) == 83 and count(session, Issue) == 9 and count(session, MeetingRating) == 7


def test_loading_twice_changes_nothing(session):
    load_seed(session, DATA)
    before = {m: count(session, m) for m in (Score, Issue, Todo, MeetingRating)}
    load_seed(session, DATA)
    assert {m: count(session, m) for m in (Score, Issue, Todo, MeetingRating)} == before


def test_a_rerun_restores_edited_rows_to_the_seed_values(session):
    load_seed(session, DATA)
    issue = session.get(Issue, "i1")
    issue.title = "edited"
    session.flush()
    load_seed(session, DATA)
    session.expire_all()
    assert session.get(Issue, "i1").title == DATA["issues"][0]["title"]


def test_ids_from_the_file_are_kept(session):
    load_seed(session, DATA)
    assert session.get(Issue, "i1") is not None and session.get(Todo, "t12") is not None


def test_meeting_links_are_derived_from_the_meeting_window(session):
    load_seed(session, DATA)
    assert session.get(Issue, "i7").solved_in_meeting_id == "mt1"
    assert session.get(Issue, "i6").solved_in_meeting_id == "mt2"
    assert session.get(Todo, "t20").created_in_meeting_id == "mt1"
    assert session.get(Todo, "t30").created_in_meeting_id == "mt2"
    assert session.get(Todo, "t1").created_in_meeting_id is None  # created outside any meeting
