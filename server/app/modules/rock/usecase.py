from app.modules.milestone.service import MilestoneService
from app.modules.rock.service import RockDetail, RockService
from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.team.scope import TeamScope
from app.modules.user.models import User


class RockUseCase:
    def __init__(self, rocks: RockService, milestones: MilestoneService, rbac: Rbac, scope: TeamScope):
        self.rocks = rocks
        self.milestones = milestones
        self.rbac = rbac
        self.scope = scope

    def list_current_rocks(self, actor: User, team_id: str) -> list[RockDetail]:
        self.rbac.require(actor, Action.LIST_ROCKS)
        self.scope.require_member(actor, team_id)
        return self._current_rocks(team_id)

    def admin_list_current_rocks(self, actor: User, team_id: str) -> list[RockDetail]:
        self.rbac.require(actor, Action.ANY_TEAM_LIST_ROCKS)
        return self._current_rocks(team_id)

    def _current_rocks(self, team_id: str) -> list[RockDetail]:
        rocks = self.rocks.list_current(team_id)
        by_rock = self.milestones.grouped_by_rock([r.id for r in rocks])
        return [RockDetail(rock=r, milestones=by_rock.get(r.id, [])) for r in rocks]
