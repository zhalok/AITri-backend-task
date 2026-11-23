from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, get_clock
from app.core.database import get_session
from app.modules.measurable.factory import get_measurable_service
from app.modules.measurable.service import MeasurableService
from app.modules.score.repository import ScoreRepository
from app.modules.score.service import ScoreService
from app.modules.score.usecase import ScoreUseCase
from app.modules.team.factory import get_access_policy
from app.modules.team.policy import AccessPolicy


def get_score_repository(session: Session = Depends(get_session)) -> ScoreRepository:
    return ScoreRepository(session)


def get_score_service(
    repo: ScoreRepository = Depends(get_score_repository), clock: Clock = Depends(get_clock)
) -> ScoreService:
    return ScoreService(repo, clock)


def get_score_usecase(
    scores: ScoreService = Depends(get_score_service),
    measurables: MeasurableService = Depends(get_measurable_service),
    policy: AccessPolicy = Depends(get_access_policy),
    clock: Clock = Depends(get_clock),
) -> ScoreUseCase:
    return ScoreUseCase(scores, measurables, policy, clock)
