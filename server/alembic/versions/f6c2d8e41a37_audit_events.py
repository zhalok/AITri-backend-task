"""audit trail of changes

Revision ID: f6c2d8e41a37
Revises: c3d8a1f6e742
Create Date: 2026-11-25 10:00:00.000000

`audit_events` records every change to the rows teammates edit concurrently (scores, issues, todos, meetings):
the operation, the old and new row, the team, who made it, and the transaction it belonged to.

It is written by a trigger, in the same transaction as the change, not by the NOTIFY listener: if the write
commits, its audit row commits with it (and rolls back with it), nothing depends on a listener being up,
there is no 8 KB payload limit, and writes made outside the API (psql, scripts) are covered too.

The API names the actor by setting the transaction-local setting `app.actor_id` (`tag_actor`). The table is
append-only: the database itself refuses updates, deletes and truncates. An UPDATE that changes nothing is not
recorded.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f6c2d8e41a37'
down_revision: Union[str, Sequence[str], None] = 'c3d8a1f6e742'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

AUDITED = ("scores", "issues", "todos", "meetings")

AUDIT_FUNCTION = """
create or replace function audit_change() returns trigger as $$
declare
    row_data record;
    the_team text;
    the_key text;
begin
    if tg_op = 'UPDATE' and to_jsonb(old) = to_jsonb(new) then
        return null;  -- nothing changed: not worth a row
    end if;
    if tg_op = 'DELETE' then row_data := old; else row_data := new; end if;

    if tg_table_name = 'scores' then
        select team_id into the_team from measurables where id = row_data.measurable_id;
        the_key := row_data.measurable_id || '|' || row_data.week_start::text;
    else  -- issues, todos, meetings
        the_team := row_data.team_id;
        the_key := row_data.id;
    end if;

    insert into audit_events (table_name, op, team_id, row_key, actor_id, old_row, new_row)
    values (
        tg_table_name, tg_op, the_team, the_key,
        nullif(current_setting('app.actor_id', true), ''),
        case when tg_op <> 'INSERT' then to_jsonb(old) end,
        case when tg_op <> 'DELETE' then to_jsonb(new) end
    );
    return null;
end;
$$ language plpgsql;
"""

IMMUTABLE_FUNCTION = """
create or replace function audit_events_immutable() returns trigger as $$
begin
    raise exception 'audit_events is append-only';
end;
$$ language plpgsql;
"""


def upgrade() -> None:
    op.create_table(
        'audit_events',
        sa.Column('id', sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=False),
        sa.Column('txid', sa.BigInteger(), server_default=sa.text('txid_current()'), nullable=False),
        sa.Column('table_name', sa.String(length=32), nullable=False),
        sa.Column('op', sa.String(length=8), nullable=False),
        sa.Column('team_id', sa.String(length=64), nullable=True),
        sa.Column('row_key', sa.String(length=200), nullable=False),
        sa.Column('actor_id', sa.String(length=64), nullable=True),
        sa.Column('old_row', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_row', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint("op in ('INSERT','UPDATE','DELETE')", name='ck_audit_op'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_events_team_id_id', 'audit_events', ['team_id', 'id'])
    op.create_index('ix_audit_events_row', 'audit_events', ['table_name', 'row_key', 'id'])

    op.execute(AUDIT_FUNCTION)
    op.execute(IMMUTABLE_FUNCTION)
    op.execute("create trigger trg_audit_events_no_change before update or delete on audit_events "
               "for each row execute function audit_events_immutable()")
    op.execute("create trigger trg_audit_events_no_truncate before truncate on audit_events "
               "for each statement execute function audit_events_immutable()")
    for table in AUDITED:
        op.execute(f"create trigger trg_{table}_audit after insert or update or delete on {table} "
                   f"for each row execute function audit_change()")


def downgrade() -> None:
    for table in AUDITED:
        op.execute(f"drop trigger if exists trg_{table}_audit on {table}")
    op.execute("drop trigger if exists trg_audit_events_no_truncate on audit_events")
    op.execute("drop trigger if exists trg_audit_events_no_change on audit_events")
    op.execute("drop function if exists audit_events_immutable()")
    op.execute("drop function if exists audit_change()")
    op.drop_index('ix_audit_events_row', table_name='audit_events')
    op.drop_index('ix_audit_events_team_id_id', table_name='audit_events')
    op.drop_table('audit_events')
