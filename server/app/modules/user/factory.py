from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.user.repository import UserRepository
from app.modules.user.service import UserService
from app.modules.user.usecase import UserUseCase


def get_user_repository(session: Session = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)


def get_user_usecase(users: UserService = Depends(get_user_service)) -> UserUseCase:
    return UserUseCase(users)
