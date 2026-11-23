from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.team.service import TeamService
from app.modules.user.models import User
from app.modules.user.service import UserService


class UserUseCase:
    def __init__(self, users: UserService, teams: TeamService, rbac: Rbac):
        self.users = users
        self.teams = teams
        self.rbac = rbac

    def list_users(self, actor: User) -> list[User]:
        self.rbac.require(actor, Action.LIST_USERS)
        return self.teams.members_of_my_teams(actor)

    def list_all_users(self, actor: User) -> list[User]:
        self.rbac.require(actor, Action.LIST_ALL_USERS)
        return self.users.list_users()
