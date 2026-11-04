"""Authentication schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import BaseSchema


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseSchema):
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_superuser: bool
    email_verified: bool
    locale: str
    avatar_url: Optional[str] = None


class MembershipOut(BaseSchema):
    id: str
    organization_id: str
    organization_name: str
    organization_code: str
    role: str
    is_active: bool


class MeOut(BaseSchema):
    user: UserOut
    memberships: list[MembershipOut] = []


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str
