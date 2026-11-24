from unittest.mock import MagicMock

import pytest

from app.core.errors import ForbiddenError, UnauthorizedError
from app.modules.realtime.service import TeamSubscriptionAccess
from app.modules.team.scope import TeamScope
from tests.helpers import make_user


def access(user=None, member_of=()):
    auth = MagicMock()
    if user is None:
        auth.user_from_token.side_effect = UnauthorizedError("Invalid or expired token")
    else:
        auth.user_from_token.return_value = user
    teams = MagicMock()
    teams.is_member.side_effect = lambda user_id, team_id: team_id in member_of
    return TeamSubscriptionAccess(auth, TeamScope(teams))


def test_a_member_may_listen_to_their_own_team():
    user = make_user("u2")
    assert access(user, member_of={"t1"}).authorize("tok", "t1") is user


def test_a_member_may_not_listen_to_another_team_even_by_guessing_its_id():
    with pytest.raises(ForbiddenError):
        access(make_user("u2"), member_of={"t1"}).authorize("tok", "t2")


def test_observers_may_listen_to_their_team_but_no_other():
    obs = make_user("u9", role="observer")
    assert access(obs, member_of={"t1"}).authorize("tok", "t1") is obs
    with pytest.raises(ForbiddenError):
        access(obs, member_of={"t1"}).authorize("tok", "t2")


def test_admins_may_listen_to_any_team():
    admin = make_user("a1", role="admin")
    assert access(admin, member_of=set()).authorize("tok", "t3") is admin


def test_a_bad_token_is_rejected():
    with pytest.raises(UnauthorizedError):
        access(None).authorize("bad", "t1")
