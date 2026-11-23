from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.todo.factory import get_todo_usecase
from app.modules.todo.schemas import TodoCreate, TodoOut
from app.modules.todo.usecase import TodoUseCase
from app.modules.user.models import User

router = APIRouter(tags=["todos"])


@router.get("/teams/{team_id}/todos", response_model=list[TodoOut])
def list_todos(team_id: str, actor: User = Depends(get_current_user), uc: TodoUseCase = Depends(get_todo_usecase)):
    return uc.list_todos(actor, team_id)


@router.post("/issues/{issue_id}/todos", response_model=TodoOut, status_code=201)
def create_todo_for_issue(
    issue_id: str, body: TodoCreate, actor: User = Depends(get_current_user), uc: TodoUseCase = Depends(get_todo_usecase)
):
    """Due in 7 days (company time), linked to the Issue."""
    return uc.create_for_issue(actor, issue_id, body.title, body.owner_id)


@router.post("/todos/{todo_id}/done", response_model=TodoOut)
def mark_done(todo_id: str, actor: User = Depends(get_current_user), uc: TodoUseCase = Depends(get_todo_usecase)):
    return uc.set_done(actor, todo_id, True)


@router.delete("/todos/{todo_id}/done", response_model=TodoOut)
def undo_done(todo_id: str, actor: User = Depends(get_current_user), uc: TodoUseCase = Depends(get_todo_usecase)):
    return uc.set_done(actor, todo_id, False)
