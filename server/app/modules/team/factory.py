from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.team.policy import AccessPolicy
from app.modules.team.repository import TeamRepository
from app.modules.team.service import TeamService
from app.modules.team.usecase import TeamUseCase


def get_team_repository(session: Session = Depends(get_session)) -> TeamRepository:
    return TeamRepository(session)


def get_team_service(repo: TeamRepository = Depends(get_team_repository)) -> TeamService:
    return TeamService(repo)


def get_access_policy(teams: TeamService = Depends(get_team_service)) -> AccessPolicy:
    return AccessPolicy(teams)


def get_team_usecase(
    teams: TeamService = Depends(get_team_service),
    policy: AccessPolicy = Depends(get_access_policy),
) -> TeamUseCase:
    return TeamUseCase(teams, policy)
