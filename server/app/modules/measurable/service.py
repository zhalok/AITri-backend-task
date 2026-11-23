from app.core.base import BaseService
from app.modules.measurable.models import Measurable
from app.modules.measurable.repository import MeasurableRepository


class MeasurableService(BaseService[Measurable]):
    entity_name = "Measurable"
    repository: MeasurableRepository

    def list_for_team(self, team_id: str) -> list[Measurable]:
        return self.repository.list_for_team(team_id)
