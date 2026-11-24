from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.audit.models import AuditEvent
from app.modules.audit.service import AuditService
from app.modules.user.models import User


class AuditUseCase:
    """Admin-only, any team (the audit trail is for investigating, not for teams to browse)."""

    def __init__(self, audit: AuditService, rbac: Rbac):
        self.audit = audit
        self.rbac = rbac

    def list_events(self, actor: User, **filters) -> list[AuditEvent]:
        self.rbac.require(actor, Action.LIST_AUDIT_EVENTS)
        return self.audit.list_events(**filters)
