from datetime import date
from decimal import Decimal

from app.core.clock import Clock
from app.core.errors import DomainValidationError
from app.modules.score.models import Score
from app.modules.score.repository import ScoreRepository


class ScoreService:
    def __init__(self, repository: ScoreRepository, clock: Clock):
        self.repository = repository
        self.clock = clock

    def scores_by_measurable(self, measurable_ids: list[str], weeks: list[date]) -> dict[str, dict[date, Decimal]]:
        out: dict[str, dict[date, Decimal]] = {m: {} for m in measurable_ids}
        if measurable_ids:
            for s in self.repository.list_for(measurable_ids, weeks):
                out[s.measurable_id][s.week_start] = s.value
        return out

    def set_score(self, measurable_id: str, week_start: date, value: Decimal) -> Score:
        if week_start.weekday() != 0:
            raise DomainValidationError("week_start must be a Monday")
        if week_start not in self.clock.last_n_weeks(13):
            raise DomainValidationError("week_start must be within the last 13 weeks, up to the current week")
        return self.repository.upsert(measurable_id, week_start, value)
