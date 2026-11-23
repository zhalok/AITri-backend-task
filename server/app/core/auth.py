from fastapi import Depends, Header

from app.core.errors import UnauthorizedError
from app.modules.user.factory import get_user_service
from app.modules.user.models import User
from app.modules.user.service import UserService


def get_current_user(
    x_user_id: str | None = Header(default=None),
    users: UserService = Depends(get_user_service),
) -> User:
    """Seeded user switcher: the caller identifies itself with X-User-Id."""
    if not x_user_id:
        raise UnauthorizedError("Missing X-User-Id header")
    user = users.repository.get(x_user_id)
    if user is None:
        raise UnauthorizedError("Unknown user")
    return user
