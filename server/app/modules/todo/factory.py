from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, get_clock
from app.core.database import get_session
from app.modules.issue.factory import get_issue_service
from app.modules.issue.service import IssueService
from app.modules.meeting.factory import get_meeting_service
from app.modules.meeting.service import MeetingService
from app.modules.team.factory import get_team_scope, get_team_service
from app.core.rbac import Rbac, get_rbac
from app.modules.team.scope import TeamScope
from app.modules.team.service import TeamService
from app.modules.todo.repository import TodoRepository
from app.modules.todo.service import TodoService
from app.modules.todo.usecase import TodoUseCase


def get_todo_repository(session: Session = Depends(get_session)) -> TodoRepository:
    return TodoRepository(session)


def get_todo_service(repo: TodoRepository = Depends(get_todo_repository), clock: Clock = Depends(get_clock)) -> TodoService:
    return TodoService(repo, clock)


def get_todo_usecase(
    todos: TodoService = Depends(get_todo_service),
    issues: IssueService = Depends(get_issue_service),
    teams: TeamService = Depends(get_team_service),
    meetings: MeetingService = Depends(get_meeting_service),
    rbac: Rbac = Depends(get_rbac), scope: TeamScope = Depends(get_team_scope),
) -> TodoUseCase:
    return TodoUseCase(todos, issues, teams, meetings, rbac, scope)
