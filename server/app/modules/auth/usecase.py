from app.modules.auth.schemas import TokenOut
from app.modules.auth.service import AuthService


class AuthUseCase:
    def __init__(self, auth: AuthService):
        self.auth = auth

    def login(self, email: str) -> TokenOut:
        user = self.auth.authenticate(email)
        token, ttl = self.auth.issue_token(user)
        return TokenOut(access_token=token, expires_in=ttl, user=user)
