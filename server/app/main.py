from fastapi import Depends, FastAPI

from app.core.auth import get_current_user

from app.core.errors import register_error_handlers
from app.modules.auth.controller import router as auth_router
from app.modules.issue.controller import router as issue_router
from app.modules.measurable.controller import router as measurable_router
from app.modules.meeting.controller import router as meeting_router
from app.modules.rock.controller import router as rock_router
from app.modules.score.controller import router as score_router
from app.modules.team.controller import router as team_router
from app.modules.todo.controller import router as todo_router
from app.modules.user.controller import router as user_router


def create_app() -> FastAPI:
    """Application factory. Per-request wiring is done by each module's factory.py via Depends."""
    app = FastAPI(title="Level 10 Meeting API", version="0.1.0")
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
    return app


app = create_app()
