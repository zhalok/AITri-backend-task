from datetime import date, datetime, timezone

import pytest

from app.core.errors import DomainValidationError
from app.modules.todo.service import TodoService
from tests.fakes import FakeTodoRepo
from tests.helpers import NOW, make_clock, make_todo, utc


@pytest.fixture
def repo():
    return FakeTodoRepo()


@pytest.fixture
def service(repo, clock):
    return TodoService(repo, clock)


# ---- overdue: not done AND due date before today (today = APP_NOW's date in company time) ---------

@pytest.mark.parametrize(
    "due,done_at,expected",
    [
        (date(2026, 11, 10), None, True),    # due yesterday
        (date(2026, 11, 11), None, False),   # due today is NOT overdue
        (date(2026, 11, 12), None, False),   # due tomorrow
        (date(2026, 11, 10), NOW, False),    # overdue date but done
        (date(2026, 1, 1), NOW, False),
    ],
)
def test_is_overdue(service, due, done_at, expected):
    assert service.is_overdue(make_todo(due_date=due, done_at=done_at)) is expected


@pytest.mark.parametrize(
    "now_utc,today_in_chicago,overdue_if_due_nov_11",
    [
        ("2026-11-12T05:59:59Z", date(2026, 11, 11), False),  # 23:59:59 Nov 11 in Chicago (CST, UTC-6)
        ("2026-11-12T06:00:00Z", date(2026, 11, 12), True),   # midnight Nov 12 in Chicago
    ],
)
def test_today_is_the_date_in_company_time_not_utc(repo, now_utc, today_in_chicago, overdue_if_due_nov_11):
    service = TodoService(repo, make_clock(now_utc))
    assert service.clock.today() == today_in_chicago
    assert service.is_overdue(make_todo(due_date=date(2026, 11, 11))) is overdue_if_due_nov_11


def test_view_carries_the_computed_flag(service):
    view = service.view(make_todo(due_date=date(2026, 11, 1)))
    assert view.is_overdue is True and view.todo.id == "td1"


# ---- create ---------------------------------------------------------------------------------------

def test_create_for_issue_is_due_in_7_days_and_linked(service, repo):
    todo = service.create_for_issue("t1", "i1", "u2", "Call the vendor", "mt1", {"u2", "u3"})
    assert todo.due_date == date(2026, 11, 18)  # today (Nov 11) + 7
    assert (todo.source_issue_id, todo.created_in_meeting_id, todo.owner_id) == ("i1", "mt1", "u2")
    assert todo.created_at == NOW and todo.done_at is None
    assert repo.items == [todo]


def test_due_date_is_7_calendar_days_after_today_in_company_time(repo):
    # 03:00 UTC on Nov 12 is still Nov 11 in Chicago, so due = Nov 18, not Nov 19.
    service = TodoService(repo, make_clock("2026-11-12T03:00:00Z"))
    assert service.create_for_issue("t1", "i1", "u2", "x", None, {"u2"}).due_date == date(2026, 11, 18)


def test_create_without_a_meeting(service):
    assert service.create_for_issue("t1", "i1", "u2", "x", None, {"u2"}).created_in_meeting_id is None


def test_create_rejects_an_owner_who_is_not_eligible(service, repo):
    with pytest.raises(DomainValidationError):
        service.create_for_issue("t1", "i1", "observer_1", "x", None, {"u2", "u3"})
    assert repo.items == []


# ---- done / undo ----------------------------------------------------------------------------------

def test_mark_done_sets_the_done_time(service, repo):
    todo = service.set_done(make_todo(), True)
    assert todo.done_at == NOW and repo.saves == 1


def test_marking_done_again_keeps_the_original_done_time(service):
    original = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
    assert service.set_done(make_todo(done_at=original), True).done_at == original


def test_undo_clears_the_done_time(service):
    assert service.set_done(make_todo(done_at=NOW), False).done_at is None


def test_undo_on_an_open_todo_is_a_no_op(service):
    assert service.set_done(make_todo(), False).done_at is None


def test_list_for_team(service, repo):
    repo.items = [make_todo(id="a", team_id="t1"), make_todo(id="b", team_id="t2")]
    assert [t.id for t in service.list_for_team("t1")] == ["a"]
