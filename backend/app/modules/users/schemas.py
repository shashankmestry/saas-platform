from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    auth_user_id: UUID
    email: EmailStr
    display_name: str | None
    avatar_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
