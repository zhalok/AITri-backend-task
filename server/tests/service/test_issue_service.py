from datetime import date

import pytest

from app.core.errors import ConflictError, DomainValidationError, NotFoundError
from app.modules.issue.service import IssueService
from tests.fakes import FakeIssueRepo
from tests.helpers import NOW, make_issue, make_measurable, utc


@pytest.fixture
def repo():
    return FakeIssueRepo()


@pytest.fixture
def service(repo, clock):
    return IssueService(repo, clock)


def test_get_or_raise_is_a_404_for_unknown_ids(service):
    with pytest.raises(NotFoundError):
        service.get_or_raise("nope")


def test_create_sets_owner_timestamp_and_starts_unsolved(service, repo):
    issue = service.create("t1", "u2", "Hiring is slow", 4)
    assert (issue.team_id, issue.owner_id, issue.title, issue.priority) == ("t1", "u2", "Hiring is slow", 4)
    assert issue.created_at == NOW  # APP_NOW, not the system clock
    assert issue.solved_at is None and issue.resolution_note is None
    assert repo.items == [issue] and len(issue.id) > 0


def test_create_allows_no_priority(service):
    assert service.create("t1", "u2", "x", None).priority is None


def test_set_priority_updates_and_clears(service, repo):
    issue = make_issue(priority=2)
    assert service.set_priority(issue, 5).priority == 5
    assert service.set_priority(issue, None).priority is None
    assert repo.saves == 2


def test_solve_records_time_note_and_meeting(service, repo):
    issue = make_issue()
    solved = service.solve(issue, "Hired two reps", "mt1")
    assert solved.solved_at == NOW
    assert solved.resolution_note == "Hired two reps"
    assert solved.solved_in_meeting_id == "mt1"
    assert repo.saves == 1


def test_solve_outside_a_meeting_has_no_meeting_id(service):
    assert service.solve(make_issue(), "done", None).solved_in_meeting_id is None


def test_solving_twice_is_a_conflict(service):
    issue = service.solve(make_issue(), "done", None)
    with pytest.raises(ConflictError):
        service.solve(issue, "again", None)


# ---- Make it an Issue ----------------------------------------------------------------------------

def test_make_it_an_issue_titles_it_with_measurable_and_week_and_owns_it_by_the_clicker(service):
    issue, created = service.make_it_an_issue("u3", make_measurable(name="New deals closed"), date(2026, 11, 2))
    assert created is True
    assert issue.title == "New deals closed — week of 2026-11-02"
    assert issue.owner_id == "u3" and issue.team_id == "t1"
    assert (issue.source_measurable_id, issue.source_week_start) == ("m1", date(2026, 11, 2))


def test_make_it_an_issue_twice_returns_the_same_issue(service, repo):
    first, created1 = service.make_it_an_issue("u2", make_measurable(), date(2026, 11, 2))
    second, created2 = service.make_it_an_issue("u3", make_measurable(), date(2026, 11, 2))
    assert (created1, created2) == (True, False)
    assert second.id == first.id
    assert second.owner_id == "u2"  # the original owner is kept
    assert len(repo.items) == 1


def test_a_solved_issue_no_longer_blocks_a_new_one_for_the_same_week(service, repo):
    first, _ = service.make_it_an_issue("u2", make_measurable(), date(2026, 11, 2))
    service.solve(first, "fixed", None)
    second, created = service.make_it_an_issue("u2", make_measurable(), date(2026, 11, 2))
    assert created is True and second.id != first.id


def test_different_measurables_or_weeks_are_different_issues(service, repo):
    service.make_it_an_issue("u2", make_measurable(id="m1"), date(2026, 11, 2))
    service.make_it_an_issue("u2", make_measurable(id="m2"), date(2026, 11, 2))
    service.make_it_an_issue("u2", make_measurable(id="m1"), date(2026, 10, 26))
    assert len(repo.items) == 3


@pytest.mark.parametrize("week", [date(2026, 11, 3), date(2026, 11, 8), date(2026, 11, 10)])  # Tue, Sun, Tue
def test_make_it_an_issue_rejects_a_week_that_is_not_a_monday(service, week):
    with pytest.raises(DomainValidationError):
        service.make_it_an_issue("u2", make_measurable(), week)


@pytest.mark.parametrize("week", [date(2026, 8, 10), date(2026, 11, 16), date(2027, 1, 4)])
def test_make_it_an_issue_rejects_weeks_outside_the_13_week_window(service, week):
    with pytest.raises(DomainValidationError):
        service.make_it_an_issue("u2", make_measurable(), week)


@pytest.mark.parametrize("week", [date(2026, 8, 17), date(2026, 11, 9)])  # oldest and current week
def test_make_it_an_issue_accepts_the_window_boundaries(service, week):
    _, created = service.make_it_an_issue("u2", make_measurable(), week)
    assert created is True


def test_window_moves_with_the_clock(repo):
    later = IssueService(repo, __import__("tests.helpers", fromlist=["make_clock"]).make_clock(utc("2026-11-16T15:00:00Z")))
    _, created = later.make_it_an_issue("u2", make_measurable(), date(2026, 11, 16))  # now the current week
    assert created is True
