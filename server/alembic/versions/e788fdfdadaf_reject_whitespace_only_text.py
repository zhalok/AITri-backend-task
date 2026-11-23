"""reject whitespace only text

Revision ID: e788fdfdadaf
Revises: 2b110f28ce9f
Create Date: 2026-11-23 15:14:35.289748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e788fdfdadaf'
down_revision: Union[str, Sequence[str], None] = '2b110f28ce9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # btrim() only trims spaces, so tab/newline-only text slipped through. \S = any non-whitespace character.
    # Keep the explicit IS NOT NULL: a CHECK passes when its expression is NULL, and NULL ~ '\S' is NULL.
    op.drop_constraint("ck_issue_title_not_blank", "issues", type_="check")
    op.create_check_constraint("ck_issue_title_not_blank", "issues", r"title ~ '\S'")
    op.drop_constraint("ck_issue_solved_has_note", "issues", type_="check")
    op.create_check_constraint(
        "ck_issue_solved_has_note", "issues",
        r"(solved_at is null and resolution_note is null)"
        r" or (solved_at is not null and resolution_note is not null and resolution_note ~ '\S')",
    )
    op.drop_constraint("ck_todo_title_not_blank", "todos", type_="check")
    op.create_check_constraint("ck_todo_title_not_blank", "todos", r"title ~ '\S'")


def downgrade() -> None:
    op.drop_constraint("ck_todo_title_not_blank", "todos", type_="check")
    op.create_check_constraint("ck_todo_title_not_blank", "todos", "length(btrim(title)) > 0")
    op.drop_constraint("ck_issue_solved_has_note", "issues", type_="check")
    op.create_check_constraint(
        "ck_issue_solved_has_note", "issues",
        "(solved_at is null and resolution_note is null)"
        " or (solved_at is not null and resolution_note is not null and length(btrim(resolution_note)) > 0)",
    )
    op.drop_constraint("ck_issue_title_not_blank", "issues", type_="check")
    op.create_check_constraint("ck_issue_title_not_blank", "issues", "length(btrim(title)) > 0")
