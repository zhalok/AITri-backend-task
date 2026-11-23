from app.modules.measurable.models import Measurable
from app.modules.measurable.service import MeasurableService
from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.team.scope import TeamScope
from app.modules.user.models import User


class MeasurableUseCase:
    def __init__(self, measurables: MeasurableService, rbac: Rbac, scope: TeamScope):
        self.measurables = measurables
        self.rbac = rbac
        self.scope = scope

    def list_for_team(self, actor: User, team_id: str) -> list[Measurable]:
        self.rbac.require(actor, Action.LIST_MEASURABLES)
        self.scope.require_member(actor, team_id)
        return self.measurables.list_for_team(team_id)

    def admin_list_for_team(self, actor: User, team_id: str) -> list[Measurable]:
        self.rbac.require(actor, Action.ANY_TEAM_LIST_MEASURABLES)
        return self.measurables.list_for_team(team_id)
