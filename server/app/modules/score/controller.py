from datetime import date

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.score.factory import get_score_usecase
from app.modules.score.schemas import ScoreIn, ScoreOut, ScorecardOut
from app.modules.score.usecase import ScoreUseCase
from app.modules.user.models import User

router = APIRouter(tags=["scores"])


@router.get("/teams/{team_id}/scorecard", response_model=ScorecardOut)
def get_scorecard(
    team_id: str, actor: User = Depends(get_current_user), uc: ScoreUseCase = Depends(get_score_usecase)
):
    return uc.get_scorecard(actor, team_id)


@router.put("/measurables/{measurable_id}/scores/{week_start}", response_model=ScoreOut)
def set_score(
    measurable_id: str,
    week_start: date,
    body: ScoreIn,
    actor: User = Depends(get_current_user),
    uc: ScoreUseCase = Depends(get_score_usecase),
):
    return uc.set_score(actor, measurable_id, week_start, body.value)
