from sqlalchemy import select

from app.core.base import BaseRepository
from app.modules.team.models import Membership, Team
from app.modules.user.models import User


class TeamRepository(BaseRepository[Team]):
    model = Team

    def list_all(self) -> list[Team]:
        return list(self.session.scalars(select(Team).order_by(Team.name)))

    def list_for_user(self, user_id: str) -> list[Team]:
        stmt = (
            select(Team)
            .join(Membership, Membership.team_id == Team.id)
            .where(Membership.user_id == user_id)
            .order_by(Team.name)
        )
        return list(self.session.scalars(stmt))

    def is_member(self, user_id: str, team_id: str) -> bool:
        return self.session.get(Membership, (user_id, team_id)) is not None

    def list_members_of_teams(self, team_ids: list[str]) -> list[User]:
        if not team_ids:
            return []
        stmt = (
            select(User)
            .join(Membership, Membership.user_id == User.id)
            .where(Membership.team_id.in_(team_ids))
            .distinct()
            .order_by(User.name, User.id)
        )
        return list(self.session.scalars(stmt))

    def list_members(self, team_id: str) -> list[User]:
        stmt = (
            select(User)
            .join(Membership, Membership.user_id == User.id)
            .where(Membership.team_id == team_id)
            .order_by(User.name)
        )
        return list(self.session.scalars(stmt))
