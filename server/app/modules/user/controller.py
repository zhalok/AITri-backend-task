from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.user.factory import get_user_usecase
from app.modules.user.models import User
from app.modules.user.schemas import UserOut
from app.modules.user.usecase import UserUseCase

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(actor: User = Depends(get_current_user), uc: UserUseCase = Depends(get_user_usecase)):
    """People who share a team with the caller. Every role."""
    return uc.list_users(actor)


@router.get("/all", response_model=list[UserOut])
def list_all_users(actor: User = Depends(get_current_user), uc: UserUseCase = Depends(get_user_usecase)):
    """Everyone in the company. Admin only (403 for other roles)."""
    return uc.list_all_users(actor)
