from app.core.clock import Clock
from app.core.errors import ConflictError
from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.issue.service import IssueService
from app.modules.measurable.rules import measurable_status
from app.modules.measurable.service import MeasurableService
from app.modules.meeting.service import MeetingService
from app.modules.meeting_summary.schemas import (
    CreatedTodoOut, MeasurableStatusOut, MeetingSummaryOut, PersonOut, RatingSummaryOut, SolvedIssueOut,
)
from app.modules.score.service import ScoreService
from app.modules.team.scope import TeamScope
from app.modules.todo.service import TodoService
from app.modules.user.models import User
from app.modules.user.service import UserService


class MeetingSummaryUseCase:
    """The summary of an ended meeting, assembled from the meeting and the team's data."""

    def __init__(
        self, meetings: MeetingService, issues: IssueService, todos: TodoService, measurables: MeasurableService,
        scores: ScoreService, users: UserService, rbac: Rbac, scope: TeamScope, clock: Clock,
    ):
        self.meetings = meetings
        self.issues = issues
        self.todos = todos
        self.measurables = measurables
        self.scores = scores
        self.users = users
        self.rbac = rbac
        self.scope = scope
        self.clock = clock

    def get(self, actor: User, meeting_id: str) -> MeetingSummaryOut:
        self.rbac.require(actor, Action.VIEW_MEETING)
        meeting = self.meetings.get_or_raise(meeting_id)
        self.scope.require_member(actor, meeting.team_id)
        return self._summary(meeting)

    def admin_get(self, actor: User, meeting_id: str) -> MeetingSummaryOut:
        self.rbac.require(actor, Action.ANY_TEAM_VIEW_MEETING)
        return self._summary(self.meetings.get_or_raise(meeting_id))

    def _summary(self, meeting) -> MeetingSummaryOut:
        if meeting.is_active:
            raise ConflictError("The summary is available once the meeting has ended")
        state = self.meetings.state(meeting)
        # Statuses are judged as of the meeting: its last closed week, with that week's current scores.
        week = self.clock.last_closed_week_before(meeting.ended_at)
        current_week = self.clock.week_start(meeting.ended_at.astimezone(self.clock.tz).date())
        measurables = self.measurables.list_for_team(meeting.team_id)
        by_m = self.scores.scores_by_measurable([m.id for m in measurables], [week])
        rows = []
        for m in measurables:
            score = by_m[m.id].get(week)
            rows.append(MeasurableStatusOut(
                measurable_id=m.id, name=m.name, unit=m.unit, goal_type=m.goal_type, goal_value=m.goal_value,
                goal_min=m.goal_min, goal_max=m.goal_max, score=score,
                status=measurable_status(m, score, week, current_week),
            ))
        people = {u.id: u for u in self.users.get_many(state.attendee_ids)}
        return MeetingSummaryOut(
            meeting_id=meeting.id, team_id=meeting.team_id, facilitator_id=meeting.facilitator_id,
            started_at=meeting.started_at, ended_at=meeting.ended_at,
            attendees=[PersonOut(id=i, name=people[i].name) for i in state.attendee_ids if i in people],
            rating=RatingSummaryOut(average=state.average_rating, count=len(state.ratings), by_user=state.ratings),
            week_start=week, measurables=rows,
            issues_solved=[
                SolvedIssueOut(id=i.id, title=i.title, owner_id=i.owner_id, solved_at=i.solved_at, resolution_note=i.resolution_note)
                for i in self.issues.solved_in_meeting(meeting.id)
            ],
            todos_created=[
                CreatedTodoOut(id=t.id, title=t.title, owner_id=t.owner_id, due_date=t.due_date, done_at=t.done_at,
                               source_issue_id=t.source_issue_id)
                for t in self.todos.created_in_meeting(meeting.id)
            ],
        )
