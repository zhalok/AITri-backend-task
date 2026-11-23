from app.core.base import BaseService
from app.modules.team.models import Team
from app.modules.team.repository import TeamRepository
from app.modules.user.models import Role, User


class TeamService(BaseService[Team]):
    entity_name = "Team"
    repository: TeamRepository

    def list_accessible(self, user: User) -> list[Team]:
        if user.role == Role.ADMIN:
            return self.repository.list_all()
        return self.repository.list_for_user(user.id)

    def has_access(self, user: User, team_id: str) -> bool:
        return user.role == Role.ADMIN or self.repository.is_member(user.id, team_id)

    def assignable_members(self, team_id: str) -> list[User]:
        """Who may own work in this team: Admins and Team Members (never Observers)."""
        return [u for u in self.repository.list_members(team_id) if u.role != Role.OBSERVER]
