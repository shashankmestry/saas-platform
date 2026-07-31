"""Reusable authentication infrastructure.

Provider-agnostic JWT helpers live here. Module-specific orchestration belongs in
`app.modules.auth`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.config import Settings, get_settings


class TokenValidationError(Exception):
    """Raised when a token cannot be verified."""


@dataclass(frozen=True, slots=True)
class VerifiedToken:
    """Verified JWT claims used by authentication modules."""

    subject: str
    email: str
    role: str
    claims: dict[str, Any]


@lru_cache
def get_jwks_client(supabase_url: str, publishable_key: str) -> PyJWKClient:
    """Return a cached JWKS client for the given Supabase project."""
    jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(
        jwks_url,
        cache_keys=True,
        headers={
            "apikey": publishable_key,
            "Authorization": f"Bearer {publishable_key}",
        },
    )


def _supabase_issuer(supabase_url: str) -> str:
    return f"{supabase_url.rstrip('/')}/auth/v1"


def verify_supabase_jwt(
    token: str,
    settings: Settings | None = None,
) -> VerifiedToken:
    """Verify a Supabase access token using cached JWKS.

    Validates signature, algorithm, issuer, audience, and expiration.
    """
    active_settings = settings or get_settings()
    issuer = _supabase_issuer(active_settings.supabase_url)

    try:
        signing_key = get_jwks_client(
            active_settings.supabase_url,
            active_settings.supabase_publishable_key,
        ).get_signing_key_from_jwt(token)

        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=issuer,
            options={
                "require": ["exp", "sub", "email", "role"],
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
            },
        )
    except jwt.PyJWTError as exc:
        raise TokenValidationError("Invalid or expired authentication token") from exc

    subject = claims.get("sub")
    email = claims.get("email")
    role = claims.get("role")

    if not subject or not email or not role:
        raise TokenValidationError("Authentication token is missing required claims")

    return VerifiedToken(
        subject=str(subject),
        email=str(email),
        role=str(role),
        claims=claims,
    )
