from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.team.factory import get_team_service
from app.core.rbac import Rbac, get_rbac
from app.modules.team.service import TeamService
from app.modules.user.repository import UserRepository
from app.modules.user.service import UserService
from app.modules.user.usecase import UserUseCase


def get_user_repository(session: Session = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)


def get_user_usecase(
    users: UserService = Depends(get_user_service),
    teams: TeamService = Depends(get_team_service),
    rbac: Rbac = Depends(get_rbac),
) -> UserUseCase:
    return UserUseCase(users, teams, rbac)
