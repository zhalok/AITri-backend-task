from app.core.base import BaseService
from app.core.clock import Clock
from app.modules.rock.models import Rock
from app.modules.rock.repository import RockRepository


class RockService(BaseService[Rock]):
    entity_name = "Rock"
    repository: RockRepository

    def __init__(self, repository: RockRepository, clock: Clock):
        super().__init__(repository)
        self.clock = clock

    def current_quarter(self) -> str:
        today = self.clock.today()
        return f"{today.year}-Q{(today.month - 1) // 3 + 1}"

    def list_current(self, team_id: str) -> list[Rock]:
        return self.repository.list_for_team(team_id, self.current_quarter())
