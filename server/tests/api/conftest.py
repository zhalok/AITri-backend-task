"""API tests: HTTP in, real controllers/use cases/services in the middle, an in-memory seeded store at the bottom.

Real parts: the FastAPI app, authentication (sign in with a seeded email, get a real JWT), RBAC, team scope, the
services and their rules. Fake part: only the repositories (tests/api/memory.py). The clock is pinned to the seed's
"now" through APP_NOW (tests/conftest.py).
"""
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_session
from app.main import create_app
from app.modules.audit.factory import get_audit_repository
from app.modules.issue.factory import get_issue_repository
from app.modules.measurable.factory import get_measurable_repository
from app.modules.meeting.factory import get_meeting_repository
from app.modules.milestone.factory import get_milestone_repository
from app.modules.rock.factory import get_rock_repository
from app.modules.score.factory import get_score_repository
from app.modules.team.factory import get_team_repository
from app.modules.todo.factory import get_todo_repository
from app.modules.user.factory import get_user_repository
from tests.api import memory

# The seed's people (seed.json): id, email, role, teams
USERS = {
    "u1": ("avery@acme.test", "admin", {"team_lead"}),
    "u2": ("blake@acme.test", "team_member", {"team_lead", "team_sales"}),
    "u3": ("casey@acme.test", "team_member", {"team_lead"}),
    "u4": ("dana@acme.test", "team_member", {"team_lead", "team_ops"}),
    "u5": ("ellis@acme.test", "observer", {"team_lead"}),
    "u6": ("finley@acme.test", "team_member", {"team_sales"}),
    "u7": ("gray@acme.test", "observer", {"team_sales"}),
    "u8": ("harper@acme.test", "team_member", {"team_ops"}),
    "u9": ("indy@acme.test", "team_member", {"team_ops"}),
}
TEAMS = ["team_lead", "team_ops", "team_sales"]


class Api:
    """A signed-in-as-anyone HTTP client. `as_user("u5").get(...)` sends that user's real token."""

    def __init__(self, client: TestClient):
        self.client = client
        self._tokens: dict[str, str] = {}

    def token(self, user_id: str) -> str:
        if user_id not in self._tokens:
            r = self.client.post("/api/auth/login", json={"email": USERS[user_id][0]})
            assert r.status_code == 200, r.text
            self._tokens[user_id] = r.json()["access_token"]
        return self._tokens[user_id]

    def call(self, user_id: str | None, method: str, path: str, **kwargs):
        headers = {} if user_id is None else {"Authorization": f"Bearer {self.token(user_id)}"}
        return self.client.request(method, f"/api{path}", headers=headers, **kwargs)


@pytest.fixture
def api():
    app = create_app()
    store = memory.seeded_store()  # fresh per test: writes never leak between tests
    app.dependency_overrides[get_session] = lambda: memory.FakeSession()
    for factory, make in (
        (get_user_repository, memory.UserRepo), (get_team_repository, memory.TeamRepo),
        (get_measurable_repository, memory.MeasurableRepo), (get_score_repository, memory.ScoreRepo),
        (get_issue_repository, memory.IssueRepo), (get_todo_repository, memory.TodoRepo),
        (get_rock_repository, memory.RockRepo), (get_milestone_repository, memory.MilestoneRepo),
    ):
        repo = make(store)
        app.dependency_overrides[factory] = lambda repo=repo: repo
    meetings = memory.MeetingRepo(store)
    app.dependency_overrides[get_meeting_repository] = lambda: meetings
    app.dependency_overrides[get_audit_repository] = lambda: memory.AuditRepo()
    return Api(TestClient(app))
