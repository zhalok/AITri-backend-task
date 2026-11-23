from sqlalchemy import select

from app.core.base import BaseRepository
from app.modules.milestone.models import Milestone


class MilestoneRepository(BaseRepository[Milestone]):
    model = Milestone

    def list_for_rocks(self, rock_ids: list[str]) -> list[Milestone]:
        if not rock_ids:
            return []
        stmt = select(Milestone).where(Milestone.rock_id.in_(rock_ids)).order_by(Milestone.due_date, Milestone.id)
        return list(self.session.scalars(stmt))
