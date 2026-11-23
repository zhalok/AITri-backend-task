from fastapi import FastAPI

from app.core.errors import register_error_handlers
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
    for router in (
        user_router, team_router, measurable_router, score_router, rock_router,
        issue_router, todo_router, meeting_router,
    ):
        app.include_router(router, prefix="/api")
    return app


app = create_app()
