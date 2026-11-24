from dataclasses import dataclass

from app.core.base import BaseService
from app.core.clock import Clock
from app.modules.milestone.models import Milestone
from app.modules.rock.models import Rock
from app.modules.rock.rules import rock_progress, rock_status
from app.modules.rock.repository import RockRepository


@dataclass
class RockDetail:
    rock: Rock
    milestones: list[Milestone]
    status: str  # computed (rules.rock_status); the Rock's own status is the seeded one
    progress: int  # whole percent


class RockService(BaseService[Rock]):
    entity_name = "Rock"
    repository: RockRepository

    def __init__(self, repository: RockRepository, clock: Clock):
        super().__init__(repository)
        self.clock = clock

    def current_quarter(self) -> str:
        today = self.clock.today()
        return f"{today.year}-Q{(today.month - 1) // 3 + 1}"

    def detail(self, rock: Rock, milestones: list[Milestone]) -> RockDetail:
        return RockDetail(
            rock=rock, milestones=milestones,
            status=rock_status(rock.status, milestones, self.clock.today()),
            progress=rock_progress(rock.status, milestones),
        )

    def list_current(self, team_id: str) -> list[Rock]:
        return self.repository.list_for_team(team_id, self.current_quarter())
