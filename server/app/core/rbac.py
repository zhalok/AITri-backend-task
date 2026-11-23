from app.core.errors import ForbiddenError
from app.core.permissions import Action, role_can
from app.modules.user.models import User


class Rbac:
    """Role-based access control, and nothing else: may this user's ROLE perform this action?

    It knows nothing about teams, resources or ownership. If an operation needs a narrower or
    wider reach, that is a different action with its own endpoint, mapped to roles in the matrix.
    """

    def require(self, user: User, action: Action) -> None:
        if not role_can(user.role, action):
            raise ForbiddenError(f"Your role ({user.role}) cannot perform '{action}'")


def get_rbac() -> Rbac:
    return Rbac()
