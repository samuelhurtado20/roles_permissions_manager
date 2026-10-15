from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    project_id: int | None = None
    role_id: int | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255)


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True