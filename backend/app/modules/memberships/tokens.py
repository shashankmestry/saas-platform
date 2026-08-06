import hashlib
import secrets


def generate_invitation_token() -> str:
    """Generate a cryptographically secure raw invitation token."""
    return secrets.token_urlsafe(32)


def hash_invitation_token(token: str) -> str:
    """Return the SHA-256 hex digest of a raw invitation token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
