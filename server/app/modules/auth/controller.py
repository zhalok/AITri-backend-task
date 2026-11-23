from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.auth.factory import get_auth_usecase
from app.modules.auth.schemas import LoginIn, TokenOut
from app.modules.auth.usecase import AuthUseCase
from app.modules.user.models import User
from app.modules.user.schemas import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, uc: AuthUseCase = Depends(get_auth_usecase)):
    """Public. Exchange a seeded user's email for a bearer token (no password)."""
    return uc.login(body.email)


@router.get("/me", response_model=UserOut)
def me(actor: User = Depends(get_current_user)):
    return actor
