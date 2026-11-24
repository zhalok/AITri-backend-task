"""The socket protocol only: auth frame, close codes, ready, and forwarding a published change.
Authorization rules are tested in tests/service/test_realtime_access.py; Redis is replaced by a fake."""
import json

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.errors import ForbiddenError, UnauthorizedError
from app.main import create_app
from app.modules.realtime import controller


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


def connect(client, monkeypatch, *, authorize=lambda token, team: None, redis=None):
    monkeypatch.setattr(controller, "authorize", authorize)
    monkeypatch.setattr(controller, "new_redis", lambda: redis or FakeRedis())
    return client.websocket_connect("/api/ws/teams/t1")


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
