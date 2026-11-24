"""The audit trail: a trigger writes one row per real change, in the same transaction, naming the actor.

These run in the repository suite's rolled-back transaction: the audit row is written by the same transaction
as the change, which is exactly what is being relied on.
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.database import tag_actor
from app.modules.audit.models import AuditEvent
from app.modules.audit.repository import AuditRepository
from app.modules.issue.models import Issue
from app.modules.meeting.models import Meeting
from app.modules.score.repository import ScoreRepository
from tests.helpers import make_issue, make_measurable, make_meeting, make_todo
from tests.repository.conftest import add

W = date(2026, 11, 2)


def events(session, **where) -> list[AuditEvent]:
    stmt = select(AuditEvent).where(AuditEvent.team_id == "t1")
    for column, value in where.items():
        stmt = stmt.where(getattr(AuditEvent, column) == value)
    return list(session.scalars(stmt.order_by(AuditEvent.id)))


@pytest.fixture
def scores(world):
    add(world, make_measurable("m1", team_id="t1", owner_id="u2"))
    return ScoreRepository(world)


def test_a_new_score_is_recorded_with_its_team_key_and_actor(scores, world):
    tag_actor(world, "u2")
    scores.upsert("m1", W, Decimal("9"))
    [e] = events(world, table_name="scores")
    assert (e.op, e.team_id, e.row_key, e.actor_id) == ("INSERT", "t1", "m1|2026-11-02", "u2")
    assert e.old_row is None and Decimal(str(e.new_row["value"])) == 9


def test_a_changed_score_records_the_value_it_replaced(scores, world):
    scores.upsert("m1", W, Decimal("9"))
    tag_actor(world, "u3")
    scores.upsert("m1", W, Decimal("12"))
    first, second = events(world, table_name="scores")
    assert second.op == "UPDATE" and second.actor_id == "u3"
    assert Decimal(str(second.old_row["value"])) == 9 and Decimal(str(second.new_row["value"])) == 12
    assert second.id > first.id


def test_saving_the_same_value_again_records_nothing(scores, world):
    scores.upsert("m1", W, Decimal("9"))
    scores.upsert("m1", W, Decimal("9"))
    assert len(events(world, table_name="scores")) == 1


def test_a_write_nobody_tagged_has_no_actor(scores, world):
    scores.upsert("m1", W, Decimal("9"))
    assert events(world, table_name="scores")[0].actor_id is None


def test_a_refused_stale_write_leaves_no_trace(scores, world):
    scores.upsert("m1", W, Decimal("12"))
    before = len(events(world))
    assert scores.set_if_seen("m1", W, Decimal("10"), Decimal("9")) is None  # it saw 9, the cell holds 12
    assert len(events(world)) == before


def test_a_lost_update_would_show_as_two_actors_overwriting_each_other(scores, world):
    """What an investigator looks for: the same row changed by different people in quick succession, each event
    carrying the value it replaced."""
    tag_actor(world, "u2"); scores.upsert("m1", W, Decimal("9"))
    tag_actor(world, "u3"); scores.upsert("m1", W, Decimal("12"))   # u3 overwrote u2's 9
    tag_actor(world, "u2"); scores.upsert("m1", W, Decimal("10"))   # u2, on a stale view, overwrote u3's 12
    chain = events(world, table_name="scores", row_key="m1|2026-11-02")
    assert [e.actor_id for e in chain] == ["u2", "u3", "u2"]
    assert [Decimal(str(e.new_row["value"])) for e in chain] == [9, 12, 10]
    assert Decimal(str(chain[2].old_row["value"])) == 12  # the value that was silently replaced is on record


def test_issue_creation_and_solving_are_both_recorded(world):
    add(world, make_issue("i1", team_id="t1", owner_id="u2"))
    issue = world.get(Issue, "i1")
    tag_actor(world, "u3")
    issue.resolution_note = "done"
    issue.solved_at = issue.created_at
    world.flush()
    created, solved = events(world, table_name="issues")
    assert (created.op, solved.op, solved.row_key, solved.actor_id) == ("INSERT", "UPDATE", "i1", "u3")
    assert created.new_row["solved_at"] is None and solved.new_row["resolution_note"] == "done"


def test_todo_done_and_undo_are_recorded(world):
    from app.modules.todo.models import Todo

    add(world, make_todo("td1", team_id="t1", owner_id="u2"))
    todo = world.get(Todo, "td1")
    todo.done_at = todo.created_at; world.flush()
    todo.done_at = None; world.flush()
    ops = [(e.op, e.new_row["done_at"] is not None) for e in events(world, table_name="todos")]
    assert ops == [("INSERT", False), ("UPDATE", True), ("UPDATE", False)]


def test_a_meeting_starting_and_ending_is_recorded(world):
    add(world, make_meeting("mt1", team_id="t1", facilitator_id="u2"))
    meeting = world.get(Meeting, "mt1")
    meeting.status, meeting.ended_at = "ended", meeting.started_at
    world.flush()
    started, ended = events(world, table_name="meetings")
    assert (started.new_row["status"], ended.old_row["status"], ended.new_row["status"]) == ("active", "active", "ended")


def test_one_transaction_shares_one_txid(scores, world):
    scores.upsert("m1", W, Decimal("9"))
    add(world, make_issue("i1", team_id="t1", owner_id="u2"))
    assert len({e.txid for e in events(world)}) == 1


@pytest.mark.parametrize("statement", [
    "update audit_events set actor_id = 'x'", "delete from audit_events", "truncate audit_events",
])
def test_the_audit_trail_is_append_only(scores, world, statement):
    scores.upsert("m1", W, Decimal("9"))
    with pytest.raises(DBAPIError, match="append-only"):
        with world.begin_nested():
            world.execute(text(statement))


def test_a_rolled_back_change_leaves_no_audit_row(db_engine):
    """The audit row belongs to the change's transaction: roll the change back and the row goes with it."""
    marker = "rb_team_audit"
    with Session(db_engine) as s:
        s.execute(text("insert into teams (id, name) values (:t, 'x')"), {"t": marker})
        s.execute(text("insert into users (id, name, email, role) values ('rb_u', 'x', 'rb@t.test', 'team_member')"))
        s.execute(text("insert into issues (id, team_id, owner_id, title, created_at) "
                       "values ('rb_i', :t, 'rb_u', 'x', now())"), {"t": marker})
        s.rollback()
    with Session(db_engine) as s:
        assert s.scalars(select(AuditEvent).where(AuditEvent.team_id == marker)).all() == []


# ---- reading it back --------------------------------------------------------------------------------------

def test_events_can_be_filtered_and_paged_newest_first(scores, world):
    for i, v in enumerate((9, 10, 11, 12)):
        tag_actor(world, "u2" if i % 2 == 0 else "u3")
        scores.upsert("m1", W, Decimal(v))
    repo = AuditRepository(world)
    newest_first = repo.list_events(team_id="t1", table_name="scores", row_key=None, actor_id=None, before_id=None, limit=100)
    assert [Decimal(str(e.new_row["value"])) for e in newest_first] == [12, 11, 10, 9]
    page = repo.list_events(team_id="t1", table_name="scores", row_key=None, actor_id=None,
                            before_id=newest_first[1].id, limit=2)
    assert [e.id for e in page] == [newest_first[2].id, newest_first[3].id]
    by_actor = repo.list_events(team_id="t1", table_name=None, row_key="m1|2026-11-02", actor_id="u3", before_id=None, limit=100)
    assert {e.actor_id for e in by_actor} == {"u3"} and len(by_actor) == 2
