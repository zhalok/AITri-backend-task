from datetime import timedelta

import pytest

from app.core.errors import ConflictError
from app.modules.meeting.models import MeetingRating
from app.modules.meeting.repository import MeetingRepository
from tests.helpers import NOW, make_meeting
from tests.repository.conftest import add, violates


@pytest.fixture
def repo(world):
    return MeetingRepository(world)


def test_add_meeting_persists_it(repo):
    m = repo.add_meeting(make_meeting("mt1"))
    assert repo.get("mt1") is m and repo.get_active_for_team("t1").id == "mt1"


def test_a_team_cannot_have_two_active_meetings(repo, world):
    repo.add_meeting(make_meeting("mt1", team_id="t1"))
    with pytest.raises(ConflictError):
        repo.add_meeting(make_meeting("mt2", team_id="t1"))
    assert repo.get("mt2") is None
    assert repo.get_active_for_team("t1").id == "mt1"  # the session is still usable afterwards


def test_the_database_enforces_one_active_meeting_per_team_on_its_own(world):
    add(world, make_meeting("a", team_id="t1"))
    violates(world, make_meeting("b", team_id="t1"))  # bypassing the repository


def test_different_teams_can_each_have_an_active_meeting(repo):
    repo.add_meeting(make_meeting("a", team_id="t1"))
    repo.add_meeting(make_meeting("b", team_id="t2"))
    assert repo.get_active_for_team("t2").id == "b"


def test_an_ended_meeting_frees_the_team_for_a_new_one(repo, world):
    old = repo.add_meeting(make_meeting("old", team_id="t1"))
    old.ended_at = NOW + timedelta(hours=1)
    world.flush()
    assert repo.get_active_for_team("t1") is None
    repo.add_meeting(make_meeting("new", team_id="t1"))
    assert repo.get_active_for_team("t1").id == "new"


def test_many_ended_meetings_may_coexist(world):
    for i in range(3):
        add(world, make_meeting(f"e{i}", ended_at=NOW + timedelta(hours=1)))


def test_a_meeting_cannot_end_before_it_started(world):
    violates(world, make_meeting("bad", ended_at=NOW - timedelta(seconds=1)))
    add(world, make_meeting("zero", ended_at=NOW))  # equal is allowed


@pytest.mark.parametrize("section", ["scorecard", "ids", "conclude"])
def test_valid_sections(world, section):
    add(world, make_meeting("ok", current_section=section))


@pytest.mark.parametrize("section", ["intro", "IDS", "", "wrapup"])
def test_invalid_sections_are_rejected(world, section):
    violates(world, make_meeting("bad", current_section=section))


# ---- attendees / ratings ------------------------------------------------------------------------

def test_adding_an_attendee_twice_is_harmless_and_ids_are_sorted(repo):
    repo.add_meeting(make_meeting("mt1"))
    for u in ("u3", "u2", "u2", "u3", "u4"):
        repo.add_attendee("mt1", u)
    assert repo.attendee_ids("mt1") == ["u2", "u3", "u4"]
    assert repo.attendee_ids("nope") == []


def test_ratings_upsert_so_an_attendee_can_change_their_mind(repo):
    repo.add_meeting(make_meeting("mt1"))
    repo.add_attendee("mt1", "u2")
    repo.add_attendee("mt1", "u3")
    repo.upsert_rating("mt1", "u2", 6)
    repo.upsert_rating("mt1", "u3", 9)
    repo.upsert_rating("mt1", "u2", 8)
    assert repo.ratings("mt1") == {"u2": 8, "u3": 9}


def test_a_non_attendee_cannot_be_rated_in_the_database(repo, world):
    repo.add_meeting(make_meeting("mt1"))
    repo.add_attendee("mt1", "u2")
    violates(world, MeetingRating(meeting_id="mt1", user_id="u3", rating=7))  # u3 never joined


@pytest.mark.parametrize("rating", [0, 11, -1, 100])
def test_ratings_must_be_1_to_10(repo, world, rating):
    repo.add_meeting(make_meeting("mt1"))
    repo.add_attendee("mt1", "u2")
    violates(world, MeetingRating(meeting_id="mt1", user_id="u2", rating=rating))


@pytest.mark.parametrize("rating", [1, 10])
def test_rating_boundaries_are_stored(repo, rating):
    repo.add_meeting(make_meeting("mt1"))
    repo.add_attendee("mt1", "u2")
    repo.upsert_rating("mt1", "u2", rating)
    assert repo.ratings("mt1") == {"u2": rating}


def test_ratings_of_a_meeting_with_none_is_empty(repo):
    repo.add_meeting(make_meeting("mt1"))
    assert repo.ratings("mt1") == {}
