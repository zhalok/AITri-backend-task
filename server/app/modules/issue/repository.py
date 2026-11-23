from datetime import date, datetime

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from app.core.base import BaseRepository
from app.modules.issue.models import Issue


class IssueRepository(BaseRepository[Issue]):
    model = Issue

    def list_unsolved(self, team_id: str) -> list[Issue]:
        """Issue order: priority 5 -> 1, no priority last; oldest first within a priority."""
        stmt = (
            select(Issue)
            .where(Issue.team_id == team_id, Issue.solved_at.is_(None))
            .order_by(Issue.priority.desc().nulls_last(), Issue.created_at.asc(), Issue.id.asc())
        )
        return list(self.session.scalars(stmt))

    def list_solved(self, team_id: str) -> list[Issue]:
        stmt = (
            select(Issue)
            .where(Issue.team_id == team_id, Issue.solved_at.is_not(None))
            .order_by(Issue.solved_at.desc(), Issue.id.asc())
        )
        return list(self.session.scalars(stmt))

    def find_unsolved_by_source(self, measurable_id: str, week_start: date) -> Issue | None:
        stmt = select(Issue).where(
            Issue.source_measurable_id == measurable_id,
            Issue.source_week_start == week_start,
            Issue.solved_at.is_(None),
        )
        return self.session.scalars(stmt).first()

    def insert_from_source_if_absent(self, values: dict) -> bool:
        """INSERT ... ON CONFLICT DO NOTHING against the partial unique index.

        Concurrent callers serialize on the index: exactly one inserts, the rest see a conflict
        and fall through to a read of the winner's committed row. Returns True if we inserted.
        """
        stmt = (
            insert(Issue)
            .values(**values)
            .on_conflict_do_nothing(
                index_elements=[Issue.source_measurable_id, Issue.source_week_start],
                index_where=text("solved_at is null and source_measurable_id is not null"),
            )
            .returning(Issue.id)
        )
        return self.session.execute(stmt).first() is not None

    def save(self) -> None:
        self.session.flush()
