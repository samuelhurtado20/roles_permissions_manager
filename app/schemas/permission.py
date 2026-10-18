from pydantic import BaseModel, Field
from datetime import datetime


class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    category: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True


class PermissionCreate(PermissionBase):
    pass


class PermissionOut(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
