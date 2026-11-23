from app.core.errors import ForbiddenError
from app.modules.team.service import TeamService
from app.modules.user.models import User


class TeamScope:
    """Data scoping for NARROW endpoints: the team in the request must be one the user belongs to.

    This is not RBAC (it depends on data, not on the role). It exists because a guessed team id
    must be refused (spec 2.5). Wide /admin endpoints are separate actions and never call it.
    """

    def __init__(self, teams: TeamService):
        self.teams = teams

    def require_member(self, user: User, team_id: str) -> None:
        if not self.teams.is_member(user.id, team_id):
            raise ForbiddenError("You are not a member of this team")
