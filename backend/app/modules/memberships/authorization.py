from collections.abc import Callable, Coroutine
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import OrganizationPermission, role_has_permission
from app.core.database import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.memberships.context import OrganizationContext
from app.modules.memberships.repository import MembershipRepository
from app.modules.organizations.repository import OrganizationRepository
from app.modules.users.models import User

_PERMISSION_DEPENDENCIES: dict[
    OrganizationPermission,
    Callable[..., Coroutine[Any, Any, OrganizationContext]],
] = {}


def _forbidden() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden",
    )


async def get_membership_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MembershipRepository:
    return MembershipRepository(session)


async def get_organization_repository_for_authz(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrganizationRepository:
    return OrganizationRepository(session)


def require_organization_permission(
    permission: OrganizationPermission,
) -> Callable[..., Coroutine[Any, Any, OrganizationContext]]:
    """FastAPI dependency factory that authorizes an organization permission."""
    cached = _PERMISSION_DEPENDENCIES.get(permission)
    if cached is not None:
        return cached

    async def dependency(
        organization_id: UUID,
        current_user: Annotated[User, Depends(get_current_user)],
        membership_repository: Annotated[
            MembershipRepository,
            Depends(get_membership_repository),
        ],
        organization_repository: Annotated[
            OrganizationRepository,
            Depends(get_organization_repository_for_authz),
        ],
    ) -> OrganizationContext:
        membership = await membership_repository.get_by_organization_and_user(
            organization_id,
            current_user.id,
        )
        if membership is None:
            raise _forbidden()

        organization = await organization_repository.get_by_id(organization_id)
        if organization is None:
            raise _forbidden()

        try:
            context = OrganizationContext.from_membership(
                user=current_user,
                organization=organization,
                membership=membership,
            )
        except ValueError as exc:
            raise _forbidden() from exc

        if not role_has_permission(context.role, permission):
            raise _forbidden()

        return context

    _PERMISSION_DEPENDENCIES[permission] = dependency
    return dependency
