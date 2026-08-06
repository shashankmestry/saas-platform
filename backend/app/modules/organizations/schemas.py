from datetime import datetime
from uuid import UUID
from zoneinfo import available_timezones

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

_VALID_TIMEZONES = available_timezones()


def _empty_to_none(value: object) -> object:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        return cleaned


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
    role: str
    permissions: list[str]


class OrganizationProfileResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    website: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    country_code: str | None = None
    timezone: str | None = None
    default_currency: str | None = None
    logo_url: str | None = None


class LogoUploadRequest(BaseModel):
    content_type: str = Field(min_length=3, max_length=100)
    file_size: int = Field(gt=0)

    @field_validator("content_type")
    @classmethod
    def normalize_content_type(cls, value: str) -> str:
        return value.strip().lower()


class LogoUploadResponse(BaseModel):
    bucket: str
    path: str
    token: str
    signed_url: str


class LogoConfirmRequest(BaseModel):
    path: str = Field(min_length=1, max_length=1024)

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Path is required")
        return cleaned


class OrganizationProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=2048)
    contact_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    country_code: str | None = None
    timezone: str | None = Field(default=None, max_length=64)
    default_currency: str | None = None

    @field_validator(
        "website",
        "contact_email",
        "phone",
        "country_code",
        "timezone",
        "default_currency",
        mode="before",
    )
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        return _empty_to_none(value)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> str | None:
        if value is None:
            raise ValueError("Organization name must not be empty")
        if not isinstance(value, str):
            raise ValueError("Organization name must be a string")
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        return cleaned

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        lowered = cleaned.lower()
        if not (lowered.startswith("http://") or lowered.startswith("https://")):
            raise ValueError("Website must be a valid URL starting with http:// or https://")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        if len(cleaned) < 3:
            raise ValueError("Phone number is too short")
        allowed = set("0123456789+()- .")
        if any(char not in allowed for char in cleaned):
            raise ValueError("Phone number contains invalid characters")
        return cleaned

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        if len(cleaned) != 2 or not cleaned.isalpha():
            raise ValueError("Country code must be a 2-letter ISO code")
        return cleaned

    @field_validator("default_currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        if len(cleaned) != 3 or not cleaned.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code")
        return cleaned

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if cleaned not in _VALID_TIMEZONES:
            raise ValueError("Timezone must be a valid IANA timezone identifier")
        return cleaned

    @model_validator(mode="after")
    def at_least_one_field(self) -> "OrganizationProfileUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self
