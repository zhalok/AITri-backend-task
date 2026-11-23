from pydantic import BaseModel, Field

from app.modules.user.schemas import UserOut


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
