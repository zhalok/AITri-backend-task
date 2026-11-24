from sqlalchemy import select

from app.core.base import BaseRepository
from app.modules.audit.models import AuditEvent


class AuditRepository(BaseRepository[AuditEvent]):
    model = AuditEvent

    def list_events(
        self, *, team_id: str | None, table_name: str | None, row_key: str | None, actor_id: str | None,
        before_id: int | None, limit: int,
    ) -> list[AuditEvent]:
        """Newest first. `before_id` pages backwards: pass the last id of the previous page."""
        stmt = select(AuditEvent)
        for column, value in (
            (AuditEvent.team_id, team_id), (AuditEvent.table_name, table_name),
            (AuditEvent.row_key, row_key), (AuditEvent.actor_id, actor_id),
        ):
            if value is not None:
                stmt = stmt.where(column == value)
        if before_id is not None:
            stmt = stmt.where(AuditEvent.id < before_id)
        return list(self.session.scalars(stmt.order_by(AuditEvent.id.desc()).limit(limit)))
