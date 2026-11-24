from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_user
from app.modules.audit.factory import get_audit_usecase
from app.modules.audit.schemas import AuditEventOut
from app.modules.audit.usecase import AuditUseCase
from app.modules.user.models import User

router = APIRouter(tags=["audit"])


@router.get("/audit-events", response_model=list[AuditEventOut])
def list_audit_events(
    team_id: str | None = None,
    table: str | None = Query(None, description="scores, issues, todos or meetings"),
    row_key: str | None = Query(None, description="the row's id; scores: '<measurable_id>|<week_start>'"),
    actor_id: str | None = None,
    before_id: int | None = Query(None, description="page backwards: the last id of the previous page"),
    limit: int = Query(100, ge=1, le=500),
    actor: User = Depends(get_current_user),
    uc: AuditUseCase = Depends(get_audit_usecase),
):
    """Admin only (any team; there is no narrower version, so no /admin twin). Every recorded change, newest first: operation, old and new row, who, and when."""
    return uc.list_events(
        actor, team_id=team_id, table_name=table, row_key=row_key, actor_id=actor_id, before_id=before_id, limit=limit
    )
