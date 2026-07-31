from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import AuthenticatedUser
from app.modules.users.exceptions import UserInactiveError
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepository:
    return UserRepository(session)


async def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository)


async def get_current_platform_user(
    authenticated_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Resolve a platform user from an authenticated JWT identity.

    Reserved for later user-management steps. Authentication endpoints must not
    depend on this helper.
    """
    try:
        return await user_service.get_or_create_from_auth(authenticated_user)
    except UserInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
