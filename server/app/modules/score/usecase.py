from datetime import date

from app.core.clock import Clock
from app.modules.measurable.service import MeasurableService
from app.modules.score.models import Score
from app.modules.score.schemas import ScorecardOut, ScorecardRow
from app.modules.score.service import ScoreService
from app.modules.team.policy import AccessPolicy
from app.modules.user.models import User


class ScoreUseCase:
    def __init__(
        self, scores: ScoreService, measurables: MeasurableService, policy: AccessPolicy, clock: Clock
    ):
        self.scores = scores
        self.measurables = measurables
        self.policy = policy
        self.clock = clock

    def get_scorecard(self, actor: User, team_id: str) -> ScorecardOut:
        self.policy.require_read(actor, team_id)
        weeks = self.clock.last_n_weeks(13)
        measurables = self.measurables.list_for_team(team_id)
        by_m = self.scores.scores_by_measurable([m.id for m in measurables], weeks)
        rows = [
            ScorecardRow(measurable=m, scores={w: by_m[m.id].get(w) for w in weeks}) for m in measurables
        ]
        return ScorecardOut(weeks=weeks, rows=rows)

    def set_score(self, actor: User, measurable_id: str, week_start: date, value) -> Score:
        measurable = self.measurables.get_or_raise(measurable_id)
        self.policy.require_write(actor, measurable.team_id)
        return self.scores.set_score(measurable_id, week_start, value)
