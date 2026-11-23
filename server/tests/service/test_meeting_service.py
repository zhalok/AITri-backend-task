import pytest

from app.core.errors import ConflictError, DomainValidationError, ForbiddenError
from app.modules.meeting.models import Section
from app.modules.meeting.service import MeetingService
from tests.fakes import FakeMeetingRepo
from tests.helpers import NOW, make_clock, make_user, utc


@pytest.fixture
def repo():
    return FakeMeetingRepo()


@pytest.fixture
def service(repo, clock):
    return MeetingService(repo, clock)


@pytest.fixture
def meeting(service):
    return service.start("t1", make_user("u2"))


def to_conclude(service, meeting):
    service.advance(meeting)
    service.advance(meeting)


# ---- start / join -----------------------------------------------------------------------------

def test_start_begins_in_scorecard_with_the_starter_as_facilitator_and_attendee(service, repo):
    m = service.start("t1", make_user("u2"))
    assert (m.team_id, m.facilitator_id, m.current_section) == ("t1", "u2", Section.SCORECARD)
    assert m.started_at == m.section_started_at == NOW and m.ended_at is None
    assert repo.attendee_ids(m.id) == ["u2"]


def test_only_one_active_meeting_per_team(service):
    service.start("t1", make_user("u2"))
    with pytest.raises(ConflictError):
        service.start("t1", make_user("u3"))


def test_another_team_can_meet_at_the_same_time(service):
    service.start("t1", make_user("u2"))
    assert service.start("t2", make_user("u3")).team_id == "t2"


def test_a_new_meeting_can_start_after_the_last_one_ended(service, meeting):
    service.end(meeting)
    assert service.start("t1", make_user("u3")).facilitator_id == "u3"


def test_join_adds_an_attendee_once(service, repo, meeting):
    service.join(meeting, make_user("u5", role="observer"))
    service.join(meeting, make_user("u5", role="observer"))
    assert repo.attendee_ids(meeting.id) == ["u2", "u5"]


def test_cannot_join_an_ended_meeting(service, meeting):
    service.end(meeting)
    with pytest.raises(DomainValidationError):
        service.join(meeting, make_user("u3"))


def test_get_active_for_team(service, meeting):
    assert service.get_active_for_team("t1") is meeting
    assert service.get_active_for_team("t2") is None


# ---- facilitator --------------------------------------------------------------------------------

def test_only_the_facilitator_passes_the_facilitator_check(service, meeting):
    service.require_facilitator(meeting, make_user("u2"))
    with pytest.raises(ForbiddenError):
        service.require_facilitator(meeting, make_user("u3"))
    with pytest.raises(ForbiddenError):
        service.require_facilitator(meeting, make_user("admin", role="admin"))


# ---- advance / end ------------------------------------------------------------------------------

def test_advance_walks_scorecard_ids_conclude(service, meeting):
    assert service.advance(meeting).current_section == Section.IDS
    assert service.advance(meeting).current_section == Section.CONCLUDE


def test_advance_restarts_the_section_timer(repo):
    clock_at = lambda iso: MeetingService(repo, make_clock(iso))  # noqa: E731
    m = clock_at("2026-11-11T15:00:00Z").start("t1", make_user("u2"))
    clock_at("2026-11-11T15:07:00Z").advance(m)
    assert m.section_started_at == utc("2026-11-11T15:07:00Z")
    assert m.started_at == utc("2026-11-11T15:00:00Z")  # meeting start never moves


def test_advance_is_allowed_even_when_the_section_is_over_time(repo):
    m = MeetingService(repo, make_clock("2026-11-11T15:00:00Z")).start("t1", make_user("u2"))
    late = MeetingService(repo, make_clock("2026-11-11T18:00:00Z"))  # 3 hours into a 5 minute section
    assert late.state(m).over_time is True
    assert late.advance(m).current_section == Section.IDS


def test_cannot_advance_past_conclude(service, meeting):
    to_conclude(service, meeting)
    with pytest.raises(ConflictError):
        service.advance(meeting)


def test_cannot_advance_an_ended_meeting(service, meeting):
    service.end(meeting)
    with pytest.raises(DomainValidationError):
        service.advance(meeting)


def test_end_can_happen_in_any_section(service, meeting):
    assert service.end(meeting).ended_at == NOW  # still in scorecard


def test_cannot_end_twice(service, meeting):
    service.end(meeting)
    with pytest.raises(DomainValidationError):
        service.end(meeting)


# ---- rating -------------------------------------------------------------------------------------

def test_rating_opens_only_in_conclude(service, meeting):
    with pytest.raises(ConflictError):
        service.rate(meeting, make_user("u2"), 8)
    service.advance(meeting)
    with pytest.raises(ConflictError):  # ids
        service.rate(meeting, make_user("u2"), 8)


def test_attendee_can_rate_and_change_it_until_the_end(service, repo, meeting):
    to_conclude(service, meeting)
    service.rate(meeting, make_user("u2"), 6)
    service.rate(meeting, make_user("u2"), 9)
    assert repo.ratings(meeting.id) == {"u2": 9}


def test_a_non_attendee_cannot_rate(service, meeting):
    to_conclude(service, meeting)
    with pytest.raises(ForbiddenError):
        service.rate(meeting, make_user("u9"), 7)


def test_cannot_rate_after_the_meeting_ended(service, meeting):
    to_conclude(service, meeting)
    service.end(meeting)
    with pytest.raises(DomainValidationError):
        service.rate(meeting, make_user("u2"), 7)


# ---- state: server-owned timer ----------------------------------------------------------------------

def state_at(repo, meeting, iso):
    return MeetingService(repo, make_clock(iso)).state(meeting)


def test_state_reports_section_duration_and_elapsed(repo):
    m = MeetingService(repo, make_clock("2026-11-11T15:00:00Z")).start("t1", make_user("u2"))
    s = state_at(repo, m, "2026-11-11T15:02:30Z")
    assert (s.current_section, s.section_duration_seconds, s.section_elapsed_seconds) == ("scorecard", 300, 150)
    assert s.over_time is False and s.ended_at is None
    assert s.attendee_ids == ["u2"] and s.facilitator_id == "u2"


@pytest.mark.parametrize(
    "iso,over",
    [("2026-11-11T15:04:59Z", False), ("2026-11-11T15:05:00Z", False), ("2026-11-11T15:05:01Z", True)],
)
def test_over_time_starts_strictly_after_the_section_duration(repo, iso, over):
    m = MeetingService(repo, make_clock("2026-11-11T15:00:00Z")).start("t1", make_user("u2"))
    assert state_at(repo, m, iso).over_time is over  # exactly 5:00 is not over time


def test_section_durations_are_5_60_10_minutes(repo):
    svc = MeetingService(repo, make_clock("2026-11-11T15:00:00Z"))
    m = svc.start("t1", make_user("u2"))
    durations = [svc.state(m).section_duration_seconds]
    svc.advance(m); durations.append(svc.state(m).section_duration_seconds)
    svc.advance(m); durations.append(svc.state(m).section_duration_seconds)
    assert durations == [300, 3600, 600]


def test_elapsed_freezes_at_the_end_of_the_meeting(repo):
    svc = MeetingService(repo, make_clock("2026-11-11T15:00:00Z"))
    m = svc.start("t1", make_user("u2"))
    MeetingService(repo, make_clock("2026-11-11T15:04:00Z")).end(m)
    s = state_at(repo, m, "2026-11-11T20:00:00Z")  # hours later
    assert s.section_elapsed_seconds == 240 and s.over_time is False and s.ended_at is not None


@pytest.mark.parametrize(
    "ratings,expected",
    [
        ([], None),                 # no ratings means no score
        ([8], 8.0),
        ([8, 9, 7], 8.0),
        ([8, 9, 8, 8], 8.3),        # 8.25 rounds half up
        ([7, 8], 7.5),
        ([9, 10, 10], 9.7),         # 9.666...
        ([1, 2], 1.5),
        ([10, 10, 9, 9, 9, 9, 9, 9], 9.3),         # 9.25 rounds half up  # 9.25 -> 9.3
    ],
)
def test_average_rating_is_one_decimal_rounded_half_up(service, repo, meeting, ratings, expected):
    for i, r in enumerate(ratings):
        repo.upsert_rating(meeting.id, f"r{i}", r)
    assert service.state(meeting).average_rating == (None if expected is None else pytest.approx(expected))
