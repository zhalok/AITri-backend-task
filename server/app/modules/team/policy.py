from app.core.errors import ForbiddenError
from app.modules.team.service import TeamService
from app.modules.user.models import User


class AccessPolicy:
    """Server-side authorization (spec 2.4). Called by use cases, never by controllers alone."""

    def __init__(self, teams: TeamService):
        self.teams = teams

    def require_read(self, user: User, team_id: str) -> None:
        if not self.teams.has_access(user, team_id):
            raise ForbiddenError("You do not have access to this team")

    def require_write(self, user: User, team_id: str) -> None:
        self.require_read(user, team_id)
        if not user.can_write:
            raise ForbiddenError("Observers have read-only access")
