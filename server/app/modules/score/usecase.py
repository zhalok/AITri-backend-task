from datetime import date

from app.core.clock import Clock
from app.core.concurrency import UNSET
from app.modules.measurable.service import MeasurableService
from app.modules.score.models import Score
from app.modules.score.service import Scorecard, ScorecardLine, ScoreService
from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.team.scope import TeamScope
from app.modules.user.models import User


class ScoreUseCase:
    def __init__(
        self, scores: ScoreService, measurables: MeasurableService, rbac: Rbac, scope: TeamScope, clock: Clock
    ):
        self.scores = scores
        self.measurables = measurables
        self.rbac = rbac
        self.scope = scope
        self.clock = clock

    def get_scorecard(self, actor: User, team_id: str) -> Scorecard:
        self.rbac.require(actor, Action.VIEW_SCORECARD)
        self.scope.require_member(actor, team_id)
        return self._scorecard(team_id)

    def admin_get_scorecard(self, actor: User, team_id: str) -> Scorecard:
        self.rbac.require(actor, Action.ANY_TEAM_VIEW_SCORECARD)
        return self._scorecard(team_id)

    def set_score(self, actor: User, measurable_id: str, week_start: date, value, seen=UNSET) -> Score:
        self.rbac.require(actor, Action.EDIT_SCORE)
        measurable = self.measurables.get_or_raise(measurable_id)
        self.scope.require_member(actor, measurable.team_id)
        return self.scores.set_score(measurable_id, week_start, value, seen)

    def admin_set_score(self, actor: User, measurable_id: str, week_start: date, value, seen=UNSET) -> Score:
        self.rbac.require(actor, Action.ANY_TEAM_EDIT_SCORE)
        self.measurables.get_or_raise(measurable_id)
        return self.scores.set_score(measurable_id, week_start, value, seen)

    def _scorecard(self, team_id: str) -> Scorecard:
        weeks = self.clock.last_n_weeks(13)
        measurables = self.measurables.list_for_team(team_id)
        by_m = self.scores.scores_by_measurable([m.id for m in measurables], weeks)
        lines = []
        for m in measurables:
            scores = {w: by_m[m.id].get(w) for w in weeks}
            lines.append(ScorecardLine(measurable=m, scores=scores, statuses=self.scores.statuses(m, scores)))
        return Scorecard(weeks=weeks, lines=lines)
