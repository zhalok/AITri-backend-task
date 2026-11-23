from app.core.base import BaseService
from app.modules.user.models import User
from app.modules.user.repository import UserRepository


class UserService(BaseService[User]):
    entity_name = "User"
    repository: UserRepository

    def list_users(self) -> list[User]:
        return self.repository.list_all()

    def get_many(self, ids: list[str]) -> list[User]:
        return self.repository.get_many(ids)
