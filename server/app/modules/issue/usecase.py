from datetime import date

from app.core.clock import Clock
from app.core.errors import DomainValidationError
from app.modules.issue.models import Issue
from app.modules.issue.service import IssueService
from app.modules.measurable.service import MeasurableService
from app.modules.meeting.service import MeetingService
from app.modules.team.policy import AccessPolicy
from app.modules.user.models import User


class IssueUseCase:
    def __init__(
        self,
        issues: IssueService,
        measurables: MeasurableService,
        meetings: MeetingService,
        policy: AccessPolicy,
        clock: Clock,
    ):
        self.issues = issues
        self.measurables = measurables
        self.meetings = meetings
        self.policy = policy
        self.clock = clock

    def list_issues(self, actor: User, team_id: str, solved: bool) -> list[Issue]:
        self.policy.require_read(actor, team_id)
        return self.issues.list_solved(team_id) if solved else self.issues.list_unsolved(team_id)

    def create(self, actor: User, team_id: str, title: str, priority: int | None) -> Issue:
        self.policy.require_write(actor, team_id)
        return self.issues.create(team_id, actor.id, title, priority)

    def set_priority(self, actor: User, issue_id: str, priority: int | None) -> Issue:
        issue = self.issues.get_or_raise(issue_id)
        self.policy.require_write(actor, issue.team_id)
        return self.issues.set_priority(issue, priority)

    def solve(self, actor: User, issue_id: str, note: str) -> Issue:
        issue = self.issues.get_or_raise(issue_id)
        self.policy.require_write(actor, issue.team_id)
        active = self.meetings.get_active_for_team(issue.team_id)
        return self.issues.solve(issue, note, active.id if active else None)

    def make_it_an_issue(self, actor: User, measurable_id: str, week_start: date) -> tuple[Issue, bool]:
        measurable = self.measurables.get_or_raise(measurable_id)
        self.policy.require_write(actor, measurable.team_id)
        if week_start.weekday() != 0 or week_start not in self.clock.last_n_weeks(13):
            raise DomainValidationError("week_start must be a Monday within the 13-week scorecard window")
        # TODO(rules): also require the cell to be off-track once the status rule module exists.
        title = f"{measurable.name} — week of {week_start.isoformat()}"
        return self.issues.get_or_create_from_source(measurable.team_id, actor.id, title, measurable_id, week_start)
