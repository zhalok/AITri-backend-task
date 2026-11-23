from sqlalchemy import select

from app.core.base import BaseRepository
from app.modules.rock.models import Rock


class RockRepository(BaseRepository[Rock]):
    model = Rock

    def list_for_team(self, team_id: str, quarter: str) -> list[Rock]:
        stmt = select(Rock).where(Rock.team_id == team_id, Rock.quarter == quarter).order_by(Rock.id)
        return list(self.session.scalars(stmt))
