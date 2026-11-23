from sqlalchemy import select

from app.core.base import BaseRepository
from app.modules.todo.models import Todo


class TodoRepository(BaseRepository[Todo]):
    model = Todo

    def list_for_team(self, team_id: str) -> list[Todo]:
        stmt = select(Todo).where(Todo.team_id == team_id).order_by(Todo.due_date, Todo.id)
        return list(self.session.scalars(stmt))

    def save(self) -> None:
        self.session.flush()
