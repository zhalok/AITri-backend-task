from fastapi import Depends

from app.core.config import Settings, get_settings
from app.modules.auth.service import AuthService
from app.modules.auth.usecase import AuthUseCase
from app.modules.user.factory import get_user_service
from app.modules.user.service import UserService


def get_auth_service(users: UserService = Depends(get_user_service), settings: Settings = Depends(get_settings)) -> AuthService:
    return AuthService(users, settings)


def get_auth_usecase(auth: AuthService = Depends(get_auth_service)) -> AuthUseCase:
    return AuthUseCase(auth)
