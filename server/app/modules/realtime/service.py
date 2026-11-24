from app.core.permissions import Action, role_can
from app.modules.auth.service import AuthService
from app.modules.team.scope import TeamScope
from app.modules.user.models import User


class TeamSubscriptionAccess:
    """May this token's user listen to this team's live changes? Same rule as reading the team over REST.

    Admins may listen to any team (the wide rule); everyone else only to a team they belong to,
    even if they guess an id.
    """

    def __init__(self, auth: AuthService, scope: TeamScope):
        self.auth = auth
        self.scope = scope

    def authorize(self, token: str, team_id: str) -> User:
        user = self.auth.user_from_token(token)  # raises UnauthorizedError
        if not role_can(user.role, Action.ANY_TEAM_VIEW_TEAM):
            self.scope.require_member(user, team_id)  # raises ForbiddenError
        return user
