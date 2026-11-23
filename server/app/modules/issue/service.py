from datetime import date

from app.core.base import BaseService, new_id
from app.core.clock import Clock
from app.core.errors import ConflictError
from app.modules.issue.models import Issue
from app.modules.issue.repository import IssueRepository


class IssueService(BaseService[Issue]):
    entity_name = "Issue"
    repository: IssueRepository

    def __init__(self, repository: IssueRepository, clock: Clock):
        super().__init__(repository)
        self.clock = clock

    def list_unsolved(self, team_id: str) -> list[Issue]:
        return self.repository.list_unsolved(team_id)

    def list_solved(self, team_id: str) -> list[Issue]:
        return self.repository.list_solved(team_id)

    def create(self, team_id: str, owner_id: str, title: str, priority: int | None) -> Issue:
        issue = Issue(
            id=new_id(), team_id=team_id, owner_id=owner_id, title=title, priority=priority,
            created_at=self.clock.now(),
        )
        return self.repository.add(issue)

    def get_or_create_from_source(
        self, team_id: str, owner_id: str, title: str, measurable_id: str, week_start: date
    ) -> tuple[Issue, bool]:
        """Returns (issue, created). Idempotent and safe under concurrent calls."""
        inserted = self.repository.insert_from_source_if_absent(
            dict(
                id=new_id(), team_id=team_id, owner_id=owner_id, title=title, priority=None,
                created_at=self.clock.now(), source_measurable_id=measurable_id, source_week_start=week_start,
            )
        )
        issue = self.repository.find_unsolved_by_source(measurable_id, week_start)
        assert issue is not None
        return issue, inserted

    def set_priority(self, issue: Issue, priority: int | None) -> Issue:
        issue.priority = priority
        self.repository.save()
        return issue

    def solve(self, issue: Issue, note: str, meeting_id: str | None) -> Issue:
        if issue.solved_at is not None:
            raise ConflictError("Issue is already solved")
        issue.solved_at = self.clock.now()
        issue.resolution_note = note
        issue.solved_in_meeting_id = meeting_id
        self.repository.save()
        return issue
