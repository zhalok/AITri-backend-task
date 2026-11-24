"""WebSocket: one socket per (browser, team). It only ever tells the client what changed.

Protocol (JSON text frames):
    client -> {"type": "auth", "token": "<jwt>"}   must be the first frame, within AUTH_TIMEOUT seconds
    server -> {"type": "ready"}                    subscribed; the client should refetch everything now
    server -> {"type": "change", "kind": "scorecard|issues|todos|meeting"}
Close codes: 4401 not authenticated, 4403 not allowed in this team.
The token travels in a frame, not the URL, so it never lands in access logs.
"""
import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import SessionLocal
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.config import get_settings
from app.core.realtime import new_redis, team_channel
from app.modules.auth.service import AuthService
from app.modules.realtime.service import TeamSubscriptionAccess
from app.modules.team.repository import TeamRepository
from app.modules.team.scope import TeamScope
from app.modules.team.service import TeamService
from app.modules.user.repository import UserRepository
from app.modules.user.service import UserService

log = logging.getLogger("realtime")
router = APIRouter(tags=["realtime"])

AUTH_TIMEOUT = 10.0


def authorize(token: str, team_id: str) -> None:
    """Short-lived session: the socket itself stays open for hours and must not hold a transaction."""
    with SessionLocal() as session:
        access = TeamSubscriptionAccess(
            AuthService(UserService(UserRepository(session)), get_settings()),
            TeamScope(TeamService(TeamRepository(session))),
        )
        access.authorize(token, team_id)


@router.websocket("/ws/teams/{team_id}")
async def team_events(ws: WebSocket, team_id: str) -> None:
    await ws.accept()
    try:
        first = json.loads(await asyncio.wait_for(ws.receive_text(), AUTH_TIMEOUT))
        if first.get("type") != "auth" or not isinstance(first.get("token"), str):
            raise UnauthorizedError("First frame must be an auth frame")
        await asyncio.to_thread(authorize, first["token"], team_id)
    except (UnauthorizedError, asyncio.TimeoutError, ValueError):
        return await ws.close(code=4401)
    except ForbiddenError:
        return await ws.close(code=4403)
    except WebSocketDisconnect:
        return

    redis = new_redis()
    pubsub = redis.pubsub()
    try:
        await pubsub.subscribe(team_channel(team_id))  # subscribe BEFORE "ready" so nothing slips between
        await ws.send_json({"type": "ready"})

        async def pump() -> None:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await ws.send_json({"type": "change", **json.loads(message["data"])})

        async def watch_client() -> None:
            while True:  # we expect nothing from the client; this just notices it going away
                await ws.receive_text()

        tasks = [asyncio.create_task(pump()), asyncio.create_task(watch_client())]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        for t in done:
            t.exception()  # consume it; a disconnect is the normal way out
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception("team socket failed")
    finally:
        await pubsub.aclose()
        await redis.aclose()
