"""Only Admins read the audit trail, and the filters reach the service untouched."""
import pytest

from app.core.errors import ForbiddenError
from app.core.rbac import Rbac
from app.modules.audit.service import MAX_LIMIT, AuditService
from app.modules.audit.usecase import AuditUseCase
from app.modules.user.models import Role
from tests.helpers import make_user


class FakeAuditRepo:
    def __init__(self):
        self.calls = []

    def list_events(self, **kwargs):
        self.calls.append(kwargs)
        return ["event"]


@pytest.fixture
def repo():
    return FakeAuditRepo()


@pytest.fixture
def uc(repo):
    return AuditUseCase(AuditService(repo), Rbac())  # type: ignore[arg-type]


def test_an_admin_can_list_events_with_filters(uc, repo):
    admin = make_user("u1", role=Role.ADMIN)
    assert uc.list_events(admin, team_id="t1", table_name="scores", limit=5) == ["event"]
    assert repo.calls[0]["team_id"] == "t1" and repo.calls[0]["table_name"] == "scores" and repo.calls[0]["limit"] == 5


@pytest.mark.parametrize("role", [Role.TEAM_MEMBER, Role.OBSERVER])
def test_members_and_observers_are_refused_before_anything_is_read(uc, repo, role):
    with pytest.raises(ForbiddenError):
        uc.list_events(make_user("u2", role=role))
    assert repo.calls == []


@pytest.mark.parametrize("asked,used", [(0, 1), (-5, 1), (100, 100), (10_000, MAX_LIMIT)])
def test_the_page_size_is_kept_within_bounds(uc, repo, asked, used):
    uc.list_events(make_user("u1", role=Role.ADMIN), limit=asked)
    assert repo.calls[0]["limit"] == used
