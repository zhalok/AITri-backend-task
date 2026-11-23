from app.modules.user.models import User
from app.modules.user.service import UserService


class UserUseCase:
    def __init__(self, users: UserService):
        self.users = users

    def list_users(self, actor: User) -> list[User]:
        # Used by the seeded user switcher; every authenticated user may see colleagues.
        return self.users.list_users()
