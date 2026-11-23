from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.rock.factory import get_rock_usecase
from app.modules.rock.schemas import RockOut
from app.modules.rock.usecase import RockUseCase
from app.modules.user.models import User

router = APIRouter(tags=["rocks"])


@router.get("/teams/{team_id}/rocks", response_model=list[RockOut])
def list_rocks(team_id: str, actor: User = Depends(get_current_user), uc: RockUseCase = Depends(get_rock_usecase)):
    """Current quarter's Rocks with their Milestones (read-only)."""
    return uc.list_current_rocks(actor, team_id)


admin_router = APIRouter(prefix="/admin", tags=["admin: any team"])


@admin_router.get("/teams/{team_id}/rocks", response_model=list[RockOut])
def admin_list_rocks(team_id: str, actor: User = Depends(get_current_user), uc: RockUseCase = Depends(get_rock_usecase)):
    return uc.admin_list_current_rocks(actor, team_id)
