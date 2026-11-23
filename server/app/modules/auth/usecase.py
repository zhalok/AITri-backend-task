from app.modules.auth.service import AuthService, LoginResult


class AuthUseCase:
    def __init__(self, auth: AuthService):
        self.auth = auth

    def login(self, email: str) -> LoginResult:
        user = self.auth.authenticate(email)
        token, ttl = self.auth.issue_token(user)
        return LoginResult(access_token=token, expires_in=ttl, user=user)
