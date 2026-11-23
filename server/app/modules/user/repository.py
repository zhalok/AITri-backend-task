from sqlalchemy import select

from app.core.base import BaseRepository
from app.modules.user.models import User


class UserRepository(BaseRepository[User]):
    model = User

    def list_all(self) -> list[User]:
        return list(self.session.scalars(select(User).order_by(User.id)))

    def get_many(self, ids: list[str]) -> list[User]:
        return list(self.session.scalars(select(User).where(User.id.in_(ids))))
