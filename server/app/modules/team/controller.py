from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.team.factory import get_team_usecase
from app.modules.team.schemas import TeamOut
from app.modules.team.usecase import TeamUseCase
from app.modules.user.models import User
from app.modules.user.schemas import UserOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
def list_teams(actor: User = Depends(get_current_user), uc: TeamUseCase = Depends(get_team_usecase)):
    return uc.list_my_teams(actor)


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: str, actor: User = Depends(get_current_user), uc: TeamUseCase = Depends(get_team_usecase)):
    return uc.get_team(actor, team_id)


@router.get("/{team_id}/members", response_model=list[UserOut])
def list_assignable_members(
    team_id: str, actor: User = Depends(get_current_user), uc: TeamUseCase = Depends(get_team_usecase)
):
    """Admins and Team Members who can own To-Dos, Issues, etc. in this team."""
    return uc.list_assignable_members(actor, team_id)
