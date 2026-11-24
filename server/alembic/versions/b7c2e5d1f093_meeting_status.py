"""meeting status

Revision ID: b7c2e5d1f093
Revises: a1f4c9d27b10
Create Date: 2026-11-24 12:00:00.000000

A readable `status` ('active' | 'ended') on meetings. It says what `ended_at` already says, so a check
constraint makes the database refuse a row where the two disagree. Plain column: no ORM relationships.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c2e5d1f093'
down_revision: Union[str, Sequence[str], None] = 'a1f4c9d27b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('meetings', sa.Column('status', sa.String(length=16), server_default='active', nullable=False))
    op.execute("update meetings set status = 'ended' where ended_at is not null")  # existing rows follow ended_at
    op.create_check_constraint('ck_meeting_status', 'meetings', "status in ('active','ended')")
    op.create_check_constraint('ck_meeting_status_matches_ended_at', 'meetings', "(status = 'active') = (ended_at is null)")


def downgrade() -> None:
    op.drop_constraint('ck_meeting_status_matches_ended_at', 'meetings', type_='check')
    op.drop_constraint('ck_meeting_status', 'meetings', type_='check')
    op.drop_column('meetings', 'status')
