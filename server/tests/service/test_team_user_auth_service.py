from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import Settings
from app.core.errors import NotFoundError, UnauthorizedError
from app.modules.auth.service import AuthService
from app.modules.team.service import TeamService
from app.modules.user.service import UserService
from tests.fakes import FakeTeamRepo, FakeUserRepo
from tests.helpers import make_team, make_user

SECRET = "unit-test-secret-unit-test-secret-32b"


# ---- teams ------------------------------------------------------------------------------------

@pytest.fixture
def people():
    return {
        "admin": make_user("u1", "admin", name="Avery"),
        "tm": make_user("u2", "team_member", name="Blake"),
        "tm_b": make_user("u3", "team_member", name="Casey"),
        "obs": make_user("u5", "observer", name="Ellis"),
        "loner": make_user("u9", "team_member", name="Zed"),
    }


@pytest.fixture
def teams(people):
    p = people
    return TeamService(FakeTeamRepo(
        teams=[make_team("t_ops", "Ops"), make_team("t_lead", "Leadership"), make_team("t_sales", "Sales")],
        users=list(p.values()),
        memberships={("u1", "t_lead"), ("u2", "t_lead"), ("u5", "t_lead"), ("u2", "t_ops"), ("u3", "t_ops")},
    ))


def test_list_for_user_is_only_their_teams_sorted(teams, people):
    assert [t.id for t in teams.list_for_user(people["tm"])] == ["t_lead", "t_ops"]


def test_an_admin_is_not_a_member_of_every_team_by_default(teams, people):
    assert [t.id for t in teams.list_for_user(people["admin"])] == ["t_lead"]  # wide reach is /teams/all
    assert [t.id for t in teams.list_all()] == ["t_lead", "t_ops", "t_sales"]


def test_is_member_is_pure_membership_and_ignores_role(teams, people):
    assert teams.is_member("u2", "t_ops") is True
    assert teams.is_member("u1", "t_ops") is False  # an Admin who is not a member
    assert teams.is_member("u9", "t_lead") is False


def test_assignable_members_exclude_observers(teams):
    assert [u.id for u in teams.assignable_members("t_lead")] == ["u1", "u2"]  # u5 is an observer


def test_members_of_my_teams_is_everyone_who_shares_a_team_with_me_without_duplicates(teams, people):
    assert [u.id for u in teams.members_of_my_teams(people["tm"])] == ["u1", "u2", "u3", "u5"]  # u2 is in two teams


def test_members_of_my_teams_always_includes_me_even_with_no_team(teams, people):
    assert [u.id for u in teams.members_of_my_teams(people["loner"])] == ["u9"]


def test_get_or_raise_unknown_team(teams):
    with pytest.raises(NotFoundError):
        teams.get_or_raise("nope")


# ---- users ------------------------------------------------------------------------------------

def test_user_lookups():
    svc = UserService(FakeUserRepo([make_user("u2", email="Blake@acme.test"), make_user("u1", "admin")]))
    assert svc.get_by_email("blake@ACME.test").id == "u2"  # case-insensitive
    assert svc.get_by_email("ghost@acme.test") is None
    assert svc.find("u1").role == "admin" and svc.find("zz") is None
    assert [u.id for u in svc.list_users()] == ["u1", "u2"]
    assert [u.id for u in svc.get_many(["u2"])] == ["u2"]


# ---- auth: sign-in and tokens -----------------------------------------------------------------------

def auth(users=None, **settings):
    users = users if users is not None else [make_user("u2", email="blake@acme.test")]
    return AuthService(UserService(FakeUserRepo(users)), Settings(jwt_secret=SECRET, **settings))


def test_authenticate_returns_the_user_for_a_known_email_in_any_case():
    assert auth().authenticate("BLAKE@acme.test").id == "u2"


def test_authenticate_rejects_an_unknown_email():
    with pytest.raises(UnauthorizedError):
        auth().authenticate("nobody@acme.test")


def test_token_round_trip_returns_the_same_user():
    svc = auth()
    user = svc.authenticate("blake@acme.test")
    token, ttl = svc.issue_token(user)
    assert ttl == 480 * 60
    assert svc.user_from_token(token).id == "u2"


def test_token_carries_subject_and_the_configured_lifetime():
    svc = auth(jwt_expire_minutes=15)
    token, ttl = svc.issue_token(make_user("u2"))
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    assert claims["sub"] == "u2" and claims["exp"] - claims["iat"] == 15 * 60 == ttl


def make_token(claims, key=SECRET, alg="HS256"):
    return jwt.encode(claims, key, algorithm=alg)


def in_hours(h):
    return datetime.now(timezone.utc) + timedelta(hours=h)


def test_an_expired_token_is_rejected():
    with pytest.raises(UnauthorizedError):
        auth().user_from_token(make_token({"sub": "u2", "exp": in_hours(-1)}))


def test_a_token_signed_with_another_secret_is_rejected():
    with pytest.raises(UnauthorizedError):
        auth().user_from_token(make_token({"sub": "u2", "exp": in_hours(1)}, key="x" * 40))


def test_an_unsigned_alg_none_token_is_rejected():
    with pytest.raises(UnauthorizedError):
        auth().user_from_token(make_token({"sub": "u2", "exp": in_hours(1)}, key=None, alg="none"))


@pytest.mark.parametrize("claims", [{"exp": in_hours(1)}, {"sub": "u2"}])  # no subject / no expiry
def test_a_token_missing_required_claims_is_rejected(claims):
    with pytest.raises(UnauthorizedError):
        auth().user_from_token(make_token(claims))


def test_garbage_is_rejected():
    with pytest.raises(UnauthorizedError):
        auth().user_from_token("not.a.token")


def test_a_valid_token_for_a_user_who_no_longer_exists_is_rejected():
    svc = auth()
    token, _ = svc.issue_token(make_user("u_deleted"))
    with pytest.raises(UnauthorizedError):
        svc.user_from_token(token)
