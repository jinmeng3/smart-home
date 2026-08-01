from pydantic import BaseModel, EmailStr

from app.schemas.account import AccountRead


class LoginRequest(BaseModel):
    account: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

    user: AccountRead
