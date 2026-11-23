from datetime import date

import pytest

from app.modules.team.repository import TeamRepository
from app.modules.todo.repository import TodoRepository
from app.modules.user.models import User
from app.modules.user.repository import UserRepository
from tests.helpers import NOW, make_issue, make_todo
from tests.repository.conftest import add, violates


# ---- teams --------------------------------------------------------------------------------------

def test_list_all_is_sorted_by_name(world):
    assert [t.name for t in TeamRepository(world).list_all()] == ["Leadership", "Ops"]


def test_list_for_user_returns_only_member_teams(world):
    repo = TeamRepository(world)
    assert [t.id for t in repo.list_for_user("u2")] == ["t1", "t2"]   # Leadership, Ops
    assert [t.id for t in repo.list_for_user("u3")] == ["t2"]
    assert repo.list_for_user("ghost") == []


def test_is_member(world):
    repo = TeamRepository(world)
    assert repo.is_member("u2", "t1") and repo.is_member("u3", "t2")
    assert not repo.is_member("u3", "t1") and not repo.is_member("u1", "t2")  # an admin is only a member where listed
    assert not repo.is_member("ghost", "t1")


def test_list_members_sorted_by_name(world):
    assert [u.id for u in TeamRepository(world).list_members("t1")] == ["u1", "u2", "u4"]  # Avery, Blake, Dana


def test_members_of_several_teams_has_no_duplicates(world):
    repo = TeamRepository(world)
    assert [u.id for u in repo.list_members_of_teams(["t1", "t2"])] == ["u1", "u2", "u3", "u4"]  # u2 is in both
    assert [u.id for u in repo.list_members_of_teams(["t2"])] == ["u2", "u3"]
    assert repo.list_members_of_teams([]) == []


# ---- users --------------------------------------------------------------------------------------

def test_get_by_email_ignores_case(world):
    repo = UserRepository(world)
    assert repo.get_by_email("BLAKE@Acme.Test").id == "u2"
    assert repo.get_by_email("blake@acme.test").id == "u2"
    assert repo.get_by_email("nobody@acme.test") is None


def test_list_all_and_get_many(world):
    repo = UserRepository(world)
    assert [u.id for u in repo.list_all()] == ["u1", "u2", "u3", "u4"]
    assert sorted(u.id for u in repo.get_many(["u4", "u1", "ghost"])) == ["u1", "u4"]


def test_emails_are_unique(world):
    violates(world, User(id="dup", name="X", email="blake@acme.test", role="team_member"))


@pytest.mark.parametrize("role", ["admin", "team_member", "observer"])
def test_valid_roles(world, role):
    add(world, User(id=f"x_{role}", name="X", email=f"{role}@x.test", role=role))


@pytest.mark.parametrize("role", ["owner", "Admin", "", "user", "OBSERVER"])
def test_invalid_roles_are_rejected_by_the_database(world, role):
    violates(world, User(id="bad", name="X", email="bad@x.test", role=role))


# ---- to-dos -------------------------------------------------------------------------------------

def test_todos_are_listed_per_team_by_due_date_then_id(world):
    add(world,
        make_todo("b", due_date=date(2026, 11, 20)), make_todo("a", due_date=date(2026, 11, 20)),
        make_todo("early", due_date=date(2026, 11, 1)), make_todo("other", team_id="t2"))
    assert [t.id for t in TodoRepository(world).list_for_team("t1")] == ["early", "a", "b"]


def test_a_todo_can_link_to_an_issue(world):
    add(world, make_issue("i1"))
    add(world, make_todo("td", source_issue_id="i1"))
    assert TodoRepository(world).get("td").source_issue_id == "i1"


def test_a_todo_cannot_link_to_a_missing_issue(world):
    violates(world, make_todo("bad", source_issue_id="ghost"))


@pytest.mark.parametrize("title", ["", "   ", "\t", "\n\n", " \t \n "])
def test_todo_title_cannot_be_blank_or_only_whitespace(world, title):
    violates(world, make_todo("bad", title=title))


def test_todo_done_state_round_trips_through_save(world):
    repo = TodoRepository(world)
    t = add(world, make_todo("td"))
    t.done_at = NOW
    repo.save()
    world.expire_all()
    assert repo.get("td").done_at == NOW
