from datetime import date

from app.modules.issue.models import Issue
from app.modules.issue.service import IssueService
from app.modules.measurable.service import MeasurableService
from app.modules.meeting.service import MeetingService
from app.modules.score.service import ScoreService
from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.team.scope import TeamScope
from app.modules.user.models import User


class IssueUseCase:
    def __init__(
        self,
        issues: IssueService,
        measurables: MeasurableService,
        meetings: MeetingService,
        scores: ScoreService,
        rbac: Rbac,
        scope: TeamScope,
    ):
        self.issues = issues
        self.measurables = measurables
        self.meetings = meetings
        self.scores = scores
        self.rbac = rbac
        self.scope = scope

    def list_issues(self, actor: User, team_id: str, solved: bool) -> list[Issue]:
        self.rbac.require(actor, Action.LIST_ISSUES)
        self.scope.require_member(actor, team_id)
        return self.issues.list_solved(team_id) if solved else self.issues.list_unsolved(team_id)

    def admin_list_issues(self, actor: User, team_id: str, solved: bool) -> list[Issue]:
        self.rbac.require(actor, Action.ANY_TEAM_LIST_ISSUES)
        return self.issues.list_solved(team_id) if solved else self.issues.list_unsolved(team_id)

    def create(self, actor: User, team_id: str, title: str, priority: int | None) -> Issue:
        self.rbac.require(actor, Action.CREATE_ISSUE)
        self.scope.require_member(actor, team_id)
        return self.issues.create(team_id, actor.id, title, priority)

    def admin_create(self, actor: User, team_id: str, title: str, priority: int | None) -> Issue:
        self.rbac.require(actor, Action.ANY_TEAM_CREATE_ISSUE)
        return self.issues.create(team_id, actor.id, title, priority)

    def set_priority(self, actor: User, issue_id: str, priority: int | None) -> Issue:
        self.rbac.require(actor, Action.SET_ISSUE_PRIORITY)
        issue = self.issues.get_or_raise(issue_id)
        self.scope.require_member(actor, issue.team_id)
        return self.issues.set_priority(issue, priority)

    def admin_set_priority(self, actor: User, issue_id: str, priority: int | None) -> Issue:
        self.rbac.require(actor, Action.ANY_TEAM_SET_ISSUE_PRIORITY)
        issue = self.issues.get_or_raise(issue_id)
        return self.issues.set_priority(issue, priority)

    def solve(self, actor: User, issue_id: str, note: str) -> Issue:
        self.rbac.require(actor, Action.SOLVE_ISSUE)
        issue = self.issues.get_or_raise(issue_id)
        self.scope.require_member(actor, issue.team_id)
        return self._solve(issue, note)

    def admin_solve(self, actor: User, issue_id: str, note: str) -> Issue:
        self.rbac.require(actor, Action.ANY_TEAM_SOLVE_ISSUE)
        issue = self.issues.get_or_raise(issue_id)
        return self._solve(issue, note)

    def make_it_an_issue(self, actor: User, measurable_id: str, week_start: date) -> tuple[Issue, bool]:
        self.rbac.require(actor, Action.MAKE_ISSUE_FROM_SCORE)
        measurable = self.measurables.get_or_raise(measurable_id)
        self.scope.require_member(actor, measurable.team_id)
        return self._make_it_an_issue(actor, measurable, week_start)

    def admin_make_it_an_issue(self, actor: User, measurable_id: str, week_start: date) -> tuple[Issue, bool]:
        self.rbac.require(actor, Action.ANY_TEAM_MAKE_ISSUE_FROM_SCORE)
        measurable = self.measurables.get_or_raise(measurable_id)
        return self._make_it_an_issue(actor, measurable, week_start)

    def _make_it_an_issue(self, actor: User, measurable, week_start: date) -> tuple[Issue, bool]:
        status = self.scores.status_for(measurable, week_start)
        return self.issues.make_it_an_issue(actor.id, measurable, week_start, status)

    def _solve(self, issue: Issue, note: str) -> Issue:
        active = self.meetings.get_active_for_team(issue.team_id)
        return self.issues.solve(issue, note, active.id if active else None)
