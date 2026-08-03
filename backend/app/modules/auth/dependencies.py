from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.exceptions import AuthenticationError
from app.modules.auth.schemas import AuthenticatedUser
from app.modules.auth.service import AuthService
from app.modules.users.dependencies import get_user_service
from app.modules.users.exceptions import UserInactiveError
from app.modules.users.models import User
from app.modules.users.service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service() -> AuthService:
    return AuthService()


async def get_authenticated_identity(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedUser:
    """Validate the Bearer token and return the JWT identity."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return auth_service.authenticate(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    identity: Annotated[AuthenticatedUser, Depends(get_authenticated_identity)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Return the platform user, provisioning one on first authenticated request."""
    try:
        return await user_service.get_or_create_user(identity)
    except UserInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
