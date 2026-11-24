import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.core.auth import get_current_user
from app.core.errors import register_error_handlers
from app.core.realtime import forward_changes, new_redis
from app.modules.audit.controller import router as audit_router
from app.modules.auth.controller import router as auth_router
from app.modules.issue.controller import admin_router as issue_admin_router
from app.modules.issue.controller import router as issue_router
from app.modules.measurable.controller import admin_router as measurable_admin_router
from app.modules.measurable.controller import router as measurable_router
from app.modules.meeting.controller import admin_router as meeting_admin_router
from app.modules.meeting.controller import router as meeting_router
from app.modules.meeting_summary.controller import admin_router as meeting_summary_admin_router
from app.modules.meeting_summary.controller import router as meeting_summary_router
from app.modules.realtime.controller import router as realtime_router
from app.modules.rock.controller import admin_router as rock_admin_router
from app.modules.rock.controller import router as rock_router
from app.modules.score.controller import admin_router as score_admin_router
from app.modules.score.controller import router as score_router
from app.modules.team.controller import admin_router as team_admin_router
from app.modules.team.controller import router as team_router
from app.modules.todo.controller import admin_router as todo_admin_router
from app.modules.todo.controller import router as todo_router
from app.modules.user.controller import router as user_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Runs the change listener for the life of the process (not started by tests that skip lifespan)."""
    redis = new_redis()
    task = asyncio.create_task(forward_changes(redis))
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await redis.aclose()


def create_app() -> FastAPI:
    """Application factory. Per-request wiring is done by each module's factory.py via Depends."""
    app = FastAPI(title="Level 10 Meeting API", version="0.1.0", lifespan=lifespan)
    register_error_handlers(app)
    # Public: sign-in only. Everything else is protected by default (fail closed):
    # the auth dependency is attached where routers are mounted, so a new route cannot forget it.
    protected = [Depends(get_current_user)]

    app.include_router(auth_router, prefix="/api")  # public: sign-in
    app.include_router(user_router, prefix="/api", dependencies=protected)
    app.include_router(team_router, prefix="/api", dependencies=protected)
    app.include_router(measurable_router, prefix="/api", dependencies=protected)
    app.include_router(score_router, prefix="/api", dependencies=protected)
    app.include_router(rock_router, prefix="/api", dependencies=protected)
    app.include_router(issue_router, prefix="/api", dependencies=protected)
    app.include_router(todo_router, prefix="/api", dependencies=protected)
    app.include_router(meeting_router, prefix="/api", dependencies=protected)
    app.include_router(meeting_summary_router, prefix="/api", dependencies=protected)
    app.include_router(audit_router, prefix="/api", dependencies=protected)  # Admin-only by RBAC (any team)
    # Authenticates itself (first frame), because browsers cannot set headers on a WebSocket.
    app.include_router(realtime_router, prefix="/api")

    # Wide scope (any team, no membership): Admin-only actions, one endpoint per narrow endpoint.
    app.include_router(team_admin_router, prefix="/api", dependencies=protected)
    app.include_router(measurable_admin_router, prefix="/api", dependencies=protected)
    app.include_router(score_admin_router, prefix="/api", dependencies=protected)
    app.include_router(rock_admin_router, prefix="/api", dependencies=protected)
    app.include_router(issue_admin_router, prefix="/api", dependencies=protected)
    app.include_router(todo_admin_router, prefix="/api", dependencies=protected)
    app.include_router(meeting_admin_router, prefix="/api", dependencies=protected)
    app.include_router(meeting_summary_admin_router, prefix="/api", dependencies=protected)
    return app


app = create_app()
