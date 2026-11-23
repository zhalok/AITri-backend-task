from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import Settings
from app.core.errors import UnauthorizedError
from app.modules.user.models import User
from app.modules.user.service import UserService


@dataclass
class LoginResult:
    access_token: str
    expires_in: int
    user: User


class AuthService:
    def __init__(self, users: UserService, settings: Settings):
        self.users = users
        self.settings = settings

    def authenticate(self, email: str) -> User:
        """Seeded-user sign-in: the email identifies the user (no password; see decision record)."""
        user = self.users.get_by_email(email)
        if user is None:
            raise UnauthorizedError("Unknown user")
        return user

    def issue_token(self, user: User) -> tuple[str, int]:
        ttl = self.settings.jwt_expire_minutes * 60
        now = datetime.now(timezone.utc)  # real clock, see Settings
        payload = {"sub": user.id, "iat": now, "exp": now + timedelta(seconds=ttl)}
        return jwt.encode(payload, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm), ttl

    def user_from_token(self, token: str) -> User:
        try:
            claims = jwt.decode(
                token, self.settings.jwt_secret, algorithms=[self.settings.jwt_algorithm],
                options={"require": ["sub", "exp"]},
            )
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid or expired token") from exc
        user = self.users.find(claims["sub"])  # re-read every request: removed users lose access at once
        if user is None:
            raise UnauthorizedError("Invalid or expired token")
        return user
