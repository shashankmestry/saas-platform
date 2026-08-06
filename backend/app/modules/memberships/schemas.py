from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.authorization import OrganizationRole
from app.shared.email import normalize_email


class InvitationCreate(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_invitation_email(cls, value: EmailStr) -> str:
        return normalize_email(str(value))


class InvitationAccept(BaseModel):
    token: str = Field(min_length=1)


class OrganizationMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    display_name: str | None
    email: str
    role: str
    created_at: datetime


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: str
    role: str
    expires_at: datetime
    created_at: datetime
    invite_url: str | None = None


class MemberRoleUpdate(BaseModel):
    role: OrganizationRole


class OwnershipTransferRequest(BaseModel):
    membership_id: UUID
