from app.modules.measurable.models import Measurable
from app.modules.measurable.service import MeasurableService
from app.modules.team.policy import AccessPolicy
from app.modules.user.models import User


class MeasurableUseCase:
    def __init__(self, measurables: MeasurableService, policy: AccessPolicy):
        self.measurables = measurables
        self.policy = policy

    def list_for_team(self, actor: User, team_id: str) -> list[Measurable]:
        self.policy.require_read(actor, team_id)
        return self.measurables.list_for_team(team_id)
