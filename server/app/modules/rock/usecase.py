from app.modules.milestone.service import MilestoneService
from app.modules.rock.schemas import RockOut
from app.modules.rock.service import RockService
from app.modules.team.policy import AccessPolicy
from app.modules.user.models import User


class RockUseCase:
    def __init__(self, rocks: RockService, milestones: MilestoneService, policy: AccessPolicy):
        self.rocks = rocks
        self.milestones = milestones
        self.policy = policy

    def list_current_rocks(self, actor: User, team_id: str) -> list[RockOut]:
        self.policy.require_read(actor, team_id)
        rocks = self.rocks.list_current(team_id)
        by_rock = self.milestones.grouped_by_rock([r.id for r in rocks])
        return [
            RockOut(
                id=r.id, team_id=r.team_id, owner_id=r.owner_id, title=r.title,
                quarter=r.quarter, status=r.status, milestones=by_rock.get(r.id, []),
            )
            for r in rocks
        ]
