from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.modules.memberships.repository import InvitationRepository, MembershipRepository
from app.modules.memberships.service import MembershipService
from app.modules.users.dependencies import get_user_repository
from app.modules.users.repository import UserRepository


async def get_membership_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MembershipRepository:
    return MembershipRepository(session)


async def get_invitation_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvitationRepository:
    return InvitationRepository(session)


async def get_membership_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    membership_repository: Annotated[
        MembershipRepository,
        Depends(get_membership_repository),
    ],
    invitation_repository: Annotated[
        InvitationRepository,
        Depends(get_invitation_repository),
    ],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MembershipService:
    return MembershipService(
        session=session,
        membership_repository=membership_repository,
        invitation_repository=invitation_repository,
        user_repository=user_repository,
        settings=settings,
    )
