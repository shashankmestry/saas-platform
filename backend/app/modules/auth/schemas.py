from pydantic import BaseModel, EmailStr


class AuthenticatedUser(BaseModel):
    """Authenticated identity derived from a verified Supabase JWT."""

    id: str
    email: EmailStr
    role: str
