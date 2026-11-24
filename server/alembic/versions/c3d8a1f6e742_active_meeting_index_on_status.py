"""one active meeting per team, keyed on status

Revision ID: c3d8a1f6e742
Revises: b7c2e5d1f093
Create Date: 2026-11-24 13:00:00.000000

The unique "one running meeting per team" index now uses `status` instead of `ended_at`. The check constraint
ck_meeting_status_matches_ended_at keeps the two equivalent, so behavior is unchanged.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d8a1f6e742'
down_revision: Union[str, Sequence[str], None] = 'b7c2e5d1f093'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('uq_one_active_meeting_per_team', table_name='meetings')
    op.create_index('uq_one_active_meeting_per_team', 'meetings', ['team_id'], unique=True,
                    postgresql_where=sa.text("status = 'active'"))


def downgrade() -> None:
    op.drop_index('uq_one_active_meeting_per_team', table_name='meetings')
    op.create_index('uq_one_active_meeting_per_team', 'meetings', ['team_id'], unique=True,
                    postgresql_where=sa.text('ended_at is null'))
