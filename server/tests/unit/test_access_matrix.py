"""Role -> actions matrix and the policy that applies it (spec 2.4)."""
import itertools

import pytest

from app.core.errors import ForbiddenError
from app.core.permissions import ANY_TEAM_OF, ROLE_ACTIONS, Action, role_can
from app.core.rbac import Rbac
from app.modules.measurable.usecase import MeasurableUseCase
from app.modules.team.scope import TeamScope
from app.modules.user.models import Role, User

READ_ACTIONS = {
    Action.LIST_USERS, Action.LIST_MY_TEAMS, Action.VIEW_TEAM, Action.LIST_TEAM_MEMBERS,
    Action.LIST_MEASURABLES, Action.VIEW_SCORECARD, Action.LIST_ROCKS, Action.LIST_ISSUES,
    Action.LIST_TODOS, Action.VIEW_ACTIVE_MEETING, Action.VIEW_MEETING, Action.JOIN_MEETING,
}
ADMIN_ONLY = {Action.LIST_ALL_TEAMS, Action.LIST_ALL_USERS} | set(ANY_TEAM_OF.values())
ROLES = list(Role)
ACTIONS = list(Action)


class FakeTeams:
    """Stands in for TeamService: a pure membership lookup."""

    def __init__(self, memberships: set[tuple[str, str]]):
        self.memberships = memberships

    def is_member(self, user_id: str, team_id: str) -> bool:
        return (user_id, team_id) in self.memberships


def user(role: Role) -> User:
    return User(id=f"u_{role}", name=role, email=f"{role}@x.test", role=role)


# ---- RBAC alone: role -> action, no teams anywhere ------------------------------------------

@pytest.mark.parametrize("role,action", itertools.product(ROLES, ACTIONS))
def test_rbac_decides_on_role_and_action_only(role, action):
    rbac = Rbac()  # constructed with nothing: it cannot know about teams
    if role_can(role, action):
        rbac.require(user(role), action)
    else:
        with pytest.raises(ForbiddenError):
            rbac.require(user(role), action)


# ---- team scope: a separate check, not RBAC ----------------------------------------------------

@pytest.mark.parametrize("role", ROLES)
def test_team_scope_is_pure_membership_and_ignores_role(role):
    u = user(role)
    scope = TeamScope(FakeTeams({(u.id, "team_a")}))  # type: ignore[arg-type]
    scope.require_member(u, "team_a")
    with pytest.raises(ForbiddenError):
        scope.require_member(u, "team_b")  # even an Admin: roles are not its concern


def test_rbac_passes_a_non_member_because_team_scope_is_not_its_job():
    Rbac().require(user(Role.TEAM_MEMBER), Action.SOLVE_ISSUE)  # role may solve: allowed, no team involved


# ---- both checks wired into a real use case (MeasurableUseCase) --------------------

class FakeMeasurables:
    def list_for_team(self, team_id):
        return []


def usecase(*members: User) -> MeasurableUseCase:
    scope = TeamScope(FakeTeams({(u.id, "team_a") for u in members}))  # type: ignore[arg-type]
    return MeasurableUseCase(FakeMeasurables(), Rbac(), scope)  # type: ignore[arg-type]


@pytest.mark.parametrize("role", ROLES)
def test_narrow_endpoint_member_passes_non_member_is_refused_even_an_admin(role):
    u = user(role)
    assert usecase(u).list_for_team(u, "team_a") == []
    with pytest.raises(ForbiddenError):
        usecase(u).list_for_team(u, "team_b")


def test_wide_endpoint_needs_the_any_team_action_and_no_membership():
    admin = user(Role.ADMIN)
    assert usecase().admin_list_for_team(admin, "any_team_at_all") == []
    for role in (Role.TEAM_MEMBER, Role.OBSERVER):
        u = user(role)
        with pytest.raises(ForbiddenError):
            usecase(u).admin_list_for_team(u, "team_a")  # a member, still refused: wrong action


def test_denied_role_never_reaches_the_membership_lookup():
    class ExplodingTeams:
        def is_member(self, *_):
            raise AssertionError("membership must not be consulted when the role is already denied")

    from app.modules.score.usecase import ScoreUseCase  # EDIT_SCORE is not an Observer action

    uc = ScoreUseCase(None, None, Rbac(), TeamScope(ExplodingTeams()), None)  # type: ignore[arg-type]
    with pytest.raises(ForbiddenError):
        uc.set_score(user(Role.OBSERVER), "m1", None, 1)  # type: ignore[arg-type]


@pytest.mark.parametrize("narrow", list(ANY_TEAM_OF))
def test_every_wide_action_is_admin_only(narrow):
    wide = ANY_TEAM_OF[narrow]
    assert [r for r in ROLES if role_can(r, wide)] == [Role.ADMIN]
