from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.measurable.factory import get_measurable_usecase
from app.modules.measurable.schemas import MeasurableOut
from app.modules.measurable.usecase import MeasurableUseCase
from app.modules.user.models import User

router = APIRouter(tags=["measurables"])


@router.get("/teams/{team_id}/measurables", response_model=list[MeasurableOut])
def list_measurables(
    team_id: str, actor: User = Depends(get_current_user), uc: MeasurableUseCase = Depends(get_measurable_usecase)
):
    return uc.list_for_team(actor, team_id)
