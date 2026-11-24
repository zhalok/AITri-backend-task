from fastapi import Depends

from app.core.clock import Clock, get_clock
from app.core.rbac import Rbac, get_rbac
from app.modules.issue.factory import get_issue_service
from app.modules.issue.service import IssueService
from app.modules.measurable.factory import get_measurable_service
from app.modules.measurable.service import MeasurableService
from app.modules.meeting.factory import get_meeting_service
from app.modules.meeting.service import MeetingService
from app.modules.meeting_summary.usecase import MeetingSummaryUseCase
from app.modules.score.factory import get_score_service
from app.modules.score.service import ScoreService
from app.modules.team.factory import get_team_scope
from app.modules.team.scope import TeamScope
from app.modules.todo.factory import get_todo_service
from app.modules.todo.service import TodoService
from app.modules.user.factory import get_user_service
from app.modules.user.service import UserService


def get_meeting_summary_usecase(
    meetings: MeetingService = Depends(get_meeting_service),
    issues: IssueService = Depends(get_issue_service),
    todos: TodoService = Depends(get_todo_service),
    measurables: MeasurableService = Depends(get_measurable_service),
    scores: ScoreService = Depends(get_score_service),
    users: UserService = Depends(get_user_service),
    rbac: Rbac = Depends(get_rbac), scope: TeamScope = Depends(get_team_scope), clock: Clock = Depends(get_clock),
) -> MeetingSummaryUseCase:
    return MeetingSummaryUseCase(meetings, issues, todos, measurables, scores, users, rbac, scope, clock)
