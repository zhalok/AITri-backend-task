from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.base import BaseRepository
from app.modules.score.models import Score


class ScoreRepository(BaseRepository[Score]):
    model = Score

    def list_for(self, measurable_ids: list[str], weeks: list[date]) -> list[Score]:
        stmt = select(Score).where(Score.measurable_id.in_(measurable_ids), Score.week_start.in_(weeks))
        return list(self.session.scalars(stmt))

    def set_if_seen(self, measurable_id: str, week_start: date, value: Decimal, seen: Decimal | None) -> Score | None:
        """Write only if the cell still holds `seen` (None = still empty). Returns None when it does not.

        Lock the row, compare, then update: the lock is held until this request's transaction ends, so two
        editors who saw the same value cannot both win. An empty cell has no row to lock, so there the
        insert itself is the arbiter: ON CONFLICT DO NOTHING lets exactly one inserter through.
        """
        if seen is None:
            stmt = (
                insert(Score)
                .values(measurable_id=measurable_id, week_start=week_start, value=value)
                .on_conflict_do_nothing(index_elements=[Score.measurable_id, Score.week_start])
                .returning(Score.measurable_id)
            )
            if self.session.execute(stmt).first() is None:
                return None
            self.session.expire_all()
            return self.session.get(Score, (measurable_id, week_start))
        current = self.session.execute(
            select(Score).where(Score.measurable_id == measurable_id, Score.week_start == week_start)
            .with_for_update().execution_options(populate_existing=True)
        ).scalar_one_or_none()
        if current is None or current.value != seen:
            return None
        current.value = value
        self.session.flush()
        return current

    def upsert(self, measurable_id: str, week_start: date, value: Decimal) -> Score:
        """Last save wins; atomic, so concurrent writers never conflict."""
        stmt = (
            insert(Score)
            .values(measurable_id=measurable_id, week_start=week_start, value=value)
            .on_conflict_do_update(index_elements=[Score.measurable_id, Score.week_start], set_={"value": value})
        )
        self.session.execute(stmt)
        self.session.flush()
        self.session.expire_all()
        return self.session.get(Score, (measurable_id, week_start))
