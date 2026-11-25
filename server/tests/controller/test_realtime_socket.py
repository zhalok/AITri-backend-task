"""The socket protocol only: auth frame, close codes, ready, and forwarding a published change.
Authorization rules are tested in tests/service/test_realtime_access.py; Redis is replaced by a fake."""
import json

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.errors import ForbiddenError, UnauthorizedError
from app.main import create_app
from tests.helpers import make_user
from app.modules.realtime import controller, presence


class FakePubSub:
    def __init__(self, messages):
        self.messages, self.channels = messages, []

    async def subscribe(self, channel):
        self.channels.append(channel)

    async def listen(self):
        for m in self.messages:
            yield {"type": "message", "data": json.dumps(m)}
        import asyncio
        await asyncio.sleep(3600)  # stay open like a real subscription

    async def aclose(self):
        pass


class FakeRedis:
    def __init__(self, messages=()):
        self.ps = FakePubSub(list(messages))

    def pubsub(self):
        return self.ps

    async def aclose(self):
        pass


@pytest.fixture
def client():
    return TestClient(create_app())


EVENTS = []


def connect(client, monkeypatch, *, path="meeting", authorize=lambda token, team: make_user("u2"), redis=None):
    EVENTS.clear()
    presence._open.clear()
    monkeypatch.setattr(controller, "join_active_meeting", lambda user, team: EVENTS.append(("join", user.id, team)))
    monkeypatch.setattr(controller, "leave_active_meeting", lambda user, team: EVENTS.append(("leave", user.id, team)))
    monkeypatch.setattr(controller, "authorize", authorize)
    monkeypatch.setattr(controller, "new_redis", lambda: redis or FakeRedis())
    return client.websocket_connect(f"/api/ws/teams/t1/{path}")


def test_authenticated_member_gets_ready_then_changes(client, monkeypatch):
    redis = FakeRedis([{"kind": "issues"}])
    with connect(client, monkeypatch, redis=redis) as ws:
        ws.send_json({"type": "auth", "token": "tok"})
        assert ws.receive_json() == {"type": "ready"}
        assert ws.receive_json() == {"type": "change", "kind": "issues"}
    assert redis.ps.channels == ["team:t1"]  # only this team's channel


def test_a_bad_token_closes_with_4401(client, monkeypatch):
    def deny(token, team):
        raise UnauthorizedError("Invalid or expired token")

    with connect(client, monkeypatch, authorize=deny) as ws:
        ws.send_json({"type": "auth", "token": "bad"})
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
    assert e.value.code == 4401


def test_a_team_you_cannot_see_closes_with_4403(client, monkeypatch):
    def deny(token, team):
        raise ForbiddenError("You are not a member of this team")

    with connect(client, monkeypatch, authorize=deny) as ws:
        ws.send_json({"type": "auth", "token": "tok"})
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
    assert e.value.code == 4403


def test_the_first_frame_must_be_auth(client, monkeypatch):
    with connect(client, monkeypatch) as ws:
        ws.send_json({"type": "hello"})
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
    assert e.value.code == 4401


def open_ws(client, monkeypatch, path):
    ws = connect(client, monkeypatch, path=path).__enter__()
    ws.send_json({"type": "auth", "token": "tok"})
    assert ws.receive_json() == {"type": "ready"}
    return ws


def settle():
    import time
    time.sleep(0.3)  # the server finishes its cleanup just after the client's close
    return list(EVENTS)


def test_the_meeting_endpoint_joins_on_connect_and_leaves_on_close(client, monkeypatch):
    ws = open_ws(client, monkeypatch, "meeting")
    assert EVENTS == [("join", "u2", "t1")]
    ws.close()
    assert settle() == [("join", "u2", "t1"), ("leave", "u2", "t1")]


def test_any_kind_of_disconnect_leaves(client, monkeypatch):
    ws = open_ws(client, monkeypatch, "meeting")
    ws.close(code=1006)  # an abnormal drop, like a lost connection
    assert ("leave", "u2", "t1") in settle()


def test_a_second_open_meeting_tab_keeps_the_user_in_until_the_last_one_closes(client, monkeypatch):
    first = open_ws(client, monkeypatch, "meeting")
    with client.websocket_connect("/api/ws/teams/t1/meeting") as second:
        second.send_json({"type": "auth", "token": "tok"})
        assert second.receive_json() == {"type": "ready"}
        first.close()
        assert ("leave", "u2", "t1") not in settle()
    assert ("leave", "u2", "t1") in settle()
