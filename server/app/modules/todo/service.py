from datetime import timedelta

from app.core.base import BaseService, new_id
from app.core.clock import Clock
from app.modules.todo.models import Todo
from app.modules.todo.repository import TodoRepository


class TodoService(BaseService[Todo]):
    entity_name = "To-Do"
    repository: TodoRepository

    def __init__(self, repository: TodoRepository, clock: Clock):
        super().__init__(repository)
        self.clock = clock

    def list_for_team(self, team_id: str) -> list[Todo]:
        return self.repository.list_for_team(team_id)

    def is_overdue(self, todo: Todo) -> bool:
        return todo.done_at is None and todo.due_date < self.clock.today()

    def create_for_issue(
        self, team_id: str, issue_id: str, owner_id: str, title: str, meeting_id: str | None
    ) -> Todo:
        todo = Todo(
            id=new_id(), team_id=team_id, owner_id=owner_id, title=title,
            due_date=self.clock.today() + timedelta(days=7),
            created_at=self.clock.now(), source_issue_id=issue_id, created_in_meeting_id=meeting_id,
        )
        return self.repository.add(todo)

    def set_done(self, todo: Todo, done: bool) -> Todo:
        if done and todo.done_at is None:
            todo.done_at = self.clock.now()
        elif not done:
            todo.done_at = None
        self.repository.save()
        return todo
