from app.modules.team.models import Team
from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.team.scope import TeamScope
from app.modules.team.service import TeamService
from app.modules.user.models import User


class TeamUseCase:
    def __init__(self, teams: TeamService, rbac: Rbac, scope: TeamScope):
        self.teams = teams
        self.rbac = rbac
        self.scope = scope

    def list_my_teams(self, actor: User) -> list[Team]:
        self.rbac.require(actor, Action.LIST_MY_TEAMS)
        return self.teams.list_for_user(actor)

    def list_all_teams(self, actor: User) -> list[Team]:
        self.rbac.require(actor, Action.LIST_ALL_TEAMS)
        return self.teams.list_all()

    def get_team(self, actor: User, team_id: str) -> Team:
        self.rbac.require(actor, Action.VIEW_TEAM)
        self.scope.require_member(actor, team_id)
        return self.teams.get_or_raise(team_id)

    def admin_get_team(self, actor: User, team_id: str) -> Team:
        self.rbac.require(actor, Action.ANY_TEAM_VIEW_TEAM)
        return self.teams.get_or_raise(team_id)

    def list_assignable_members(self, actor: User, team_id: str) -> list[User]:
        self.rbac.require(actor, Action.LIST_TEAM_MEMBERS)
        self.scope.require_member(actor, team_id)
        return self.teams.assignable_members(team_id)

    def admin_list_assignable_members(self, actor: User, team_id: str) -> list[User]:
        self.rbac.require(actor, Action.ANY_TEAM_LIST_TEAM_MEMBERS)
        return self.teams.assignable_members(team_id)
