"""Organization schemas."""
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class OrganizationBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=20)
    legal_name: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=200)
    timezone: str = Field(default="Asia/Tashkent")
    is_active: bool = True
    settings: Optional[Any] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, min_length=1, max_length=20)
    legal_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Any] = None


class OrganizationOut(BaseSchema):
    id: UUID
    name: str
    code: str
    legal_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    timezone: str
    is_active: bool
    settings: Optional[Any] = None
