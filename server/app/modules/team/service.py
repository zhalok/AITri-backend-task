from app.core.base import BaseService
from app.core.permissions import Action, role_can
from app.modules.team.models import Team
from app.modules.team.repository import TeamRepository
from app.modules.user.models import User


class TeamService(BaseService[Team]):
    entity_name = "Team"
    repository: TeamRepository

    def list_all(self) -> list[Team]:
        return self.repository.list_all()

    def list_for_user(self, user: User) -> list[Team]:
        return self.repository.list_for_user(user.id)

    def members_of_my_teams(self, user: User) -> list[User]:
        """People who share at least one team with `user` (always includes the user)."""
        team_ids = [t.id for t in self.repository.list_for_user(user.id)]
        people = {u.id: u for u in self.repository.list_members_of_teams(team_ids)}
        people.setdefault(user.id, user)
        return sorted(people.values(), key=lambda u: (u.name, u.id))

    def is_member(self, user_id: str, team_id: str) -> bool:
        """Pure membership. Knows nothing about roles."""
        return self.repository.is_member(user_id, team_id)

    def assignable_members(self, team_id: str) -> list[User]:
        """Who may own work in this team: Admins and Team Members (never Observers)."""
        return [u for u in self.repository.list_members(team_id) if role_can(u.role, Action.BE_ASSIGNED_WORK)]
