from sqlalchemy import select

from app.core.base import BaseRepository
from app.modules.measurable.models import Measurable


class MeasurableRepository(BaseRepository[Measurable]):
    model = Measurable

    def list_for_team(self, team_id: str) -> list[Measurable]:
        stmt = select(Measurable).where(Measurable.team_id == team_id).order_by(Measurable.id)
        return list(self.session.scalars(stmt))
