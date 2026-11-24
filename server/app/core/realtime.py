"""Real-time plumbing: Postgres NOTIFY -> Redis pub/sub -> WebSocket.

    DB trigger (after commit) --NOTIFY team_changes--> `forward_changes` (one task per API process)
        --PUBLISH team:{id}--> Redis --> every API worker's sockets subscribed to that team

Why two hops: NOTIFY gives "only after commit, from any writer" for free; Redis lets every API worker
(not just the one that handled the write) serve its own sockets. Events carry only what changed
(`{"kind": "issues"}`), never data, so clients refetch through the REST API and its permission checks.
"""
import asyncio
import json
import logging

import psycopg
from redis import asyncio as aioredis

from app.core.config import get_settings

log = logging.getLogger("realtime")

NOTIFY_CHANNEL = "team_changes"


def team_channel(team_id: str) -> str:
    return f"team:{team_id}"


def new_redis() -> aioredis.Redis:
    return aioredis.from_url(get_settings().redis_url, decode_responses=True)


def _psycopg_dsn() -> str:
    # SQLAlchemy URLs carry a driver suffix that libpq does not understand.
    return get_settings().database_url.replace("postgresql+psycopg://", "postgresql://", 1)


async def forward_changes(redis: aioredis.Redis) -> None:
    """Listen for database change notifications and republish each to its team's channel. Never returns.

    A dropped connection is retried forever: while it is down, events are missed, which is why every
    client refetches everything when its socket (re)connects.
    """
    backoff = 1.0
    while True:
        try:
            async with await psycopg.AsyncConnection.connect(_psycopg_dsn(), autocommit=True) as conn:
                await conn.execute(f"LISTEN {NOTIFY_CHANNEL}")
                backoff = 1.0
                async for note in conn.notifies():
                    try:
                        event = json.loads(note.payload)
                        await redis.publish(team_channel(event["team_id"]), json.dumps({"kind": event["kind"]}))
                    except Exception:  # one bad event must not stop the stream
                        log.exception("could not forward change event %r", note.payload)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("change listener lost its connection; retrying in %.0fs", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 15.0)
