from collections import defaultdict

from app.core.base import BaseService
from app.modules.milestone.models import Milestone
from app.modules.milestone.repository import MilestoneRepository


class MilestoneService(BaseService[Milestone]):
    entity_name = "Milestone"
    repository: MilestoneRepository

    def grouped_by_rock(self, rock_ids: list[str]) -> dict[str, list[Milestone]]:
        grouped: dict[str, list[Milestone]] = defaultdict(list)
        for ms in self.repository.list_for_rocks(rock_ids):
            grouped[ms.rock_id].append(ms)
        return grouped
