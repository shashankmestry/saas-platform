from app.core.config import Settings, get_settings
from app.core.security import TokenValidationError, verify_supabase_jwt
from app.modules.auth.exceptions import AuthenticationError
from app.modules.auth.schemas import AuthenticatedUser


class AuthService:
    """Orchestrates authentication using core security primitives."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def authenticate(self, token: str) -> AuthenticatedUser:
        try:
            verified = verify_supabase_jwt(token, settings=self._settings)
        except TokenValidationError as exc:
            raise AuthenticationError(str(exc)) from exc

        return AuthenticatedUser(
            id=verified.subject,
            email=verified.email,
            role=verified.role,
        )
