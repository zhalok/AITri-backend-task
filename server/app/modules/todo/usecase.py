from app.core.errors import DomainValidationError
from app.modules.issue.service import IssueService
from app.modules.meeting.service import MeetingService
from app.modules.team.policy import AccessPolicy
from app.modules.team.service import TeamService
from app.modules.todo.models import Todo
from app.modules.todo.schemas import TodoOut
from app.modules.todo.service import TodoService
from app.modules.user.models import User


class TodoUseCase:
    def __init__(
        self, todos: TodoService, issues: IssueService, teams: TeamService, meetings: MeetingService, policy: AccessPolicy
    ):
        self.todos = todos
        self.issues = issues
        self.teams = teams
        self.meetings = meetings
        self.policy = policy

    def _out(self, todo: Todo) -> TodoOut:
        out = TodoOut.model_validate(todo)
        out.is_overdue = self.todos.is_overdue(todo)
        return out

    def list_todos(self, actor: User, team_id: str) -> list[TodoOut]:
        self.policy.require_read(actor, team_id)
        return [self._out(t) for t in self.todos.list_for_team(team_id)]

    def create_for_issue(self, actor: User, issue_id: str, title: str, owner_id: str) -> TodoOut:
        issue = self.issues.get_or_raise(issue_id)
        self.policy.require_write(actor, issue.team_id)
        if owner_id not in {u.id for u in self.teams.assignable_members(issue.team_id)}:
            raise DomainValidationError("Owner must be an Admin or Team Member of this team")
        active = self.meetings.get_active_for_team(issue.team_id)
        todo = self.todos.create_for_issue(issue.team_id, issue.id, owner_id, title, active.id if active else None)
        return self._out(todo)

    def set_done(self, actor: User, todo_id: str, done: bool) -> TodoOut:
        todo = self.todos.get_or_raise(todo_id)
        self.policy.require_write(actor, todo.team_id)
        return self._out(self.todos.set_done(todo, done))
