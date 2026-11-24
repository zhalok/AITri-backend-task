"""meeting sections and change notifications

Revision ID: a1f4c9d27b10
Revises: e788fdfdadaf
Create Date: 2026-11-24 10:00:00.000000

Two things:

1. `meeting_sections`: one row per section a meeting entered (its event history).
2. Change capture. Triggers on the tables the dashboard and the meeting read call `pg_notify` with
   `{"team_id", "kind"}`. NOTIFY is delivered only when the transaction commits, so a listener never
   hears about a change that was rolled back, and it fires for any writer (API, seed script, psql).
   The API listens on the `team_changes` channel and forwards each event to Redis (app/core/realtime.py).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1f4c9d27b10'
down_revision: Union[str, Sequence[str], None] = 'e788fdfdadaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# table -> event kind the client understands (which of its queries to refresh)
TRIGGERS = {
    "scores": "scorecard",
    "measurables": "scorecard",
    "issues": "issues",
    "todos": "todos",
    "meetings": "meeting",
    "meeting_attendees": "meeting",
    "meeting_ratings": "meeting",
    "meeting_sections": "meeting",
}

FUNCTION = """
create or replace function notify_team_change() returns trigger as $$
declare
    row_data record;
    the_team text;
begin
    if tg_op = 'DELETE' then row_data := old; else row_data := new; end if;

    -- Not every table has a team_id; the others reach their team through their parent.
    if tg_table_name in ('issues', 'todos', 'meetings', 'measurables') then
        the_team := row_data.team_id;
    elsif tg_table_name = 'scores' then
        select team_id into the_team from measurables where id = row_data.measurable_id;
    else  -- meeting_attendees, meeting_ratings, meeting_sections
        select team_id into the_team from meetings where id = row_data.meeting_id;
    end if;

    if the_team is not null then
        perform pg_notify('team_changes', json_build_object('team_id', the_team, 'kind', tg_argv[0])::text);
    end if;
    return null;
end;
$$ language plpgsql;
"""


def upgrade() -> None:
    op.create_table(
        'meeting_sections',
        sa.Column('meeting_id', sa.String(length=64), nullable=False),
        sa.Column('section', sa.String(length=16), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("section in ('scorecard','ids','conclude')", name='ck_meeting_section_name'),
        sa.CheckConstraint('ended_at is null or ended_at >= started_at', name='ck_meeting_section_end_after_start'),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id']),
        sa.PrimaryKeyConstraint('meeting_id', 'section'),
    )
    op.execute(FUNCTION)
    for table, kind in TRIGGERS.items():
        op.execute(
            f"create trigger trg_{table}_notify after insert or update or delete on {table} "
            f"for each row execute function notify_team_change('{kind}')"
        )


def downgrade() -> None:
    for table in TRIGGERS:
        op.execute(f"drop trigger if exists trg_{table}_notify on {table}")
    op.execute("drop function if exists notify_team_change()")
    op.drop_table('meeting_sections')
