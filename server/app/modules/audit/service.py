from app.core.base import BaseService
from app.modules.audit.models import AuditEvent
from app.modules.audit.repository import AuditRepository

MAX_LIMIT = 500


class AuditService(BaseService[AuditEvent]):
    entity_name = "Audit event"
    repository: AuditRepository

    def list_events(
        self, *, team_id=None, table_name=None, row_key=None, actor_id=None, before_id=None, limit=100
    ) -> list[AuditEvent]:
        return self.repository.list_events(
            team_id=team_id, table_name=table_name, row_key=row_key, actor_id=actor_id,
            before_id=before_id, limit=max(1, min(limit, MAX_LIMIT)),
        )
