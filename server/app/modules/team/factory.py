from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.rbac import Rbac, get_rbac
from app.modules.team.repository import TeamRepository
from app.modules.team.scope import TeamScope
from app.modules.team.service import TeamService
from app.modules.team.usecase import TeamUseCase


def get_team_repository(session: Session = Depends(get_session)) -> TeamRepository:
    return TeamRepository(session)


def get_team_service(repo: TeamRepository = Depends(get_team_repository)) -> TeamService:
    return TeamService(repo)


def get_team_scope(teams: TeamService = Depends(get_team_service)) -> TeamScope:
    return TeamScope(teams)


def get_team_usecase(
    teams: TeamService = Depends(get_team_service),
    rbac: Rbac = Depends(get_rbac),
    scope: TeamScope = Depends(get_team_scope),
) -> TeamUseCase:
    return TeamUseCase(teams, rbac, scope)
