from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_session, tag_actor
from app.core.errors import UnauthorizedError
from app.modules.auth.factory import get_auth_service
from app.modules.auth.service import AuthService
from app.modules.user.models import User

# auto_error=False so a missing header yields our own 401 body, not FastAPI's 403.
_bearer = HTTPBearer(auto_error=False, description="Token from POST /api/auth/login")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    auth: AuthService = Depends(get_auth_service),
    session: Session = Depends(get_session),  # the request's own session: the one that will make the changes
) -> User:
    """Authentication gate. Resolves the bearer token to a User or raises 401, and tags the request's
    transaction with that user, so the audit trail knows who made each change."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Authentication required")
    user = auth.user_from_token(credentials.credentials)
    tag_actor(session, user.id)
    return user
