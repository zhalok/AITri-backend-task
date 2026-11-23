from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, get_clock
from app.core.database import get_session
from app.modules.milestone.factory import get_milestone_service
from app.modules.milestone.service import MilestoneService
from app.modules.rock.repository import RockRepository
from app.modules.rock.service import RockService
from app.modules.rock.usecase import RockUseCase
from app.modules.team.factory import get_access_policy
from app.modules.team.policy import AccessPolicy


def get_rock_repository(session: Session = Depends(get_session)) -> RockRepository:
    return RockRepository(session)


def get_rock_service(repo: RockRepository = Depends(get_rock_repository), clock: Clock = Depends(get_clock)) -> RockService:
    return RockService(repo, clock)


def get_rock_usecase(
    rocks: RockService = Depends(get_rock_service),
    milestones: MilestoneService = Depends(get_milestone_service),
    policy: AccessPolicy = Depends(get_access_policy),
) -> RockUseCase:
    return RockUseCase(rocks, milestones, policy)
