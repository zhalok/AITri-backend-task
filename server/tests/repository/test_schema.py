from alembic import command
from alembic.util.exc import CommandError
import pytest
from sqlalchemy import inspect, text


def test_models_and_migrations_have_not_drifted(db_engine, alembic_cfg):
    """`alembic check` fails if the models would produce a new migration."""
    try:
        command.check(alembic_cfg)
    except CommandError as exc:  # pragma: no cover
        pytest.fail(f"Models and migrations differ; generate a migration. {exc}")


def test_migrations_apply_and_roll_back_cleanly(db_engine, alembic_cfg):
    command.downgrade(alembic_cfg, "base")
    assert "issues" not in inspect(db_engine).get_table_names()
    command.upgrade(alembic_cfg, "head")
    assert {"issues", "todos", "meetings", "scores", "users"} <= set(inspect(db_engine).get_table_names())


def test_the_key_integrity_constraints_exist_in_the_database(db_engine):
    with db_engine.connect() as c:
        constraints = {r[0] for r in c.execute(text("select conname from pg_constraint where contype = 'c'"))}
        indexes = {r[0] for r in c.execute(text("select indexname from pg_indexes where schemaname = 'public'"))}
    assert {"ck_issue_priority", "ck_issue_solved_has_note", "ck_issue_source_pair", "ck_score_week_is_monday",
            "ck_rating_range", "ck_users_role", "ck_measurable_goal_shape", "ck_rock_quarter"} <= constraints
    assert {"uq_issue_unsolved_per_source", "uq_one_active_meeting_per_team"} <= indexes
