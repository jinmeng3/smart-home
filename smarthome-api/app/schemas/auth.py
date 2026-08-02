from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.account import AccountRead


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("account", mode="before")
    @classmethod
    def strip_account(cls, value: str) -> str:
        return value.strip()


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip()


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

    user: AccountRead
