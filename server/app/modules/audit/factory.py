from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.rbac import Rbac, get_rbac
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.audit.usecase import AuditUseCase


def get_audit_repository(session: Session = Depends(get_session)) -> AuditRepository:
    return AuditRepository(session)


def get_audit_service(repo: AuditRepository = Depends(get_audit_repository)) -> AuditService:
    return AuditService(repo)


def get_audit_usecase(audit: AuditService = Depends(get_audit_service), rbac: Rbac = Depends(get_rbac)) -> AuditUseCase:
    return AuditUseCase(audit, rbac)
