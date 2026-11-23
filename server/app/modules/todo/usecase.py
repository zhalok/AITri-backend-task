from app.core.errors import DomainValidationError
from app.modules.issue.service import IssueService
from app.modules.meeting.service import MeetingService
from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.team.scope import TeamScope
from app.modules.team.service import TeamService
from app.modules.todo.models import Todo
from app.modules.todo.schemas import TodoOut
from app.modules.todo.service import TodoService
from app.modules.user.models import User


class TodoUseCase:
    def __init__(
        self, todos: TodoService, issues: IssueService, teams: TeamService, meetings: MeetingService, rbac: Rbac, scope: TeamScope
    ):
        self.todos = todos
        self.issues = issues
        self.teams = teams
        self.meetings = meetings
        self.rbac = rbac
        self.scope = scope

    def list_todos(self, actor: User, team_id: str) -> list[TodoOut]:
        self.rbac.require(actor, Action.LIST_TODOS)
        self.scope.require_member(actor, team_id)
        return [self._out(t) for t in self.todos.list_for_team(team_id)]

    def admin_list_todos(self, actor: User, team_id: str) -> list[TodoOut]:
        self.rbac.require(actor, Action.ANY_TEAM_LIST_TODOS)
        return [self._out(t) for t in self.todos.list_for_team(team_id)]

    def create_for_issue(self, actor: User, issue_id: str, title: str, owner_id: str) -> TodoOut:
        self.rbac.require(actor, Action.CREATE_TODO)
        issue = self.issues.get_or_raise(issue_id)
        self.scope.require_member(actor, issue.team_id)
        return self._create_for_issue(issue, title, owner_id)

    def admin_create_for_issue(self, actor: User, issue_id: str, title: str, owner_id: str) -> TodoOut:
        self.rbac.require(actor, Action.ANY_TEAM_CREATE_TODO)
        issue = self.issues.get_or_raise(issue_id)
        return self._create_for_issue(issue, title, owner_id)

    def mark_done(self, actor: User, todo_id: str) -> TodoOut:
        self.rbac.require(actor, Action.MARK_TODO_DONE)
        todo = self.todos.get_or_raise(todo_id)
        self.scope.require_member(actor, todo.team_id)
        return self._out(self.todos.set_done(todo, True))

    def admin_mark_done(self, actor: User, todo_id: str) -> TodoOut:
        self.rbac.require(actor, Action.ANY_TEAM_MARK_TODO_DONE)
        return self._out(self.todos.set_done(self.todos.get_or_raise(todo_id), True))

    def undo_done(self, actor: User, todo_id: str) -> TodoOut:
        self.rbac.require(actor, Action.UNDO_TODO_DONE)
        todo = self.todos.get_or_raise(todo_id)
        self.scope.require_member(actor, todo.team_id)
        return self._out(self.todos.set_done(todo, False))

    def admin_undo_done(self, actor: User, todo_id: str) -> TodoOut:
        self.rbac.require(actor, Action.ANY_TEAM_UNDO_TODO_DONE)
        return self._out(self.todos.set_done(self.todos.get_or_raise(todo_id), False))

    def _create_for_issue(self, issue, title: str, owner_id: str) -> TodoOut:
        if owner_id not in {u.id for u in self.teams.assignable_members(issue.team_id)}:
            raise DomainValidationError("Owner must be an Admin or Team Member of this team")
        active = self.meetings.get_active_for_team(issue.team_id)
        todo = self.todos.create_for_issue(issue.team_id, issue.id, owner_id, title, active.id if active else None)
        return self._out(todo)

    def _out(self, todo: Todo) -> TodoOut:
        out = TodoOut.model_validate(todo)
        out.is_overdue = self.todos.is_overdue(todo)
        return out
