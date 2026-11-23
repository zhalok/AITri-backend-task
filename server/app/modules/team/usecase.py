from app.modules.team.models import Team
from app.modules.team.policy import AccessPolicy
from app.modules.team.service import TeamService
from app.modules.user.models import User


class TeamUseCase:
    def __init__(self, teams: TeamService, policy: AccessPolicy):
        self.teams = teams
        self.policy = policy

    def list_my_teams(self, actor: User) -> list[Team]:
        return self.teams.list_accessible(actor)

    def get_team(self, actor: User, team_id: str) -> Team:
        self.policy.require_read(actor, team_id)
        return self.teams.get_or_raise(team_id)

    def list_assignable_members(self, actor: User, team_id: str) -> list[User]:
        self.policy.require_read(actor, team_id)
        return self.teams.assignable_members(team_id)
