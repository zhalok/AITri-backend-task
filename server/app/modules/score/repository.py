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
