from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.storage import (
    OrganizationAssetsStorage,
    get_organization_assets_storage,
)
from app.modules.memberships.repository import MembershipRepository
from app.modules.organizations.repository import (
    OrganizationProfileRepository,
    OrganizationRepository,
)
from app.modules.organizations.service import OrganizationService
from app.modules.plans.repository import OrganizationPlanRepository


async def get_organization_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrganizationRepository:
    return OrganizationRepository(session)


async def get_organization_profile_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrganizationProfileRepository:
    return OrganizationProfileRepository(session)


async def get_membership_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MembershipRepository:
    return MembershipRepository(session)


async def get_organization_plan_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrganizationPlanRepository:
    return OrganizationPlanRepository(session)


async def get_organization_storage(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OrganizationAssetsStorage:
    return await get_organization_assets_storage(settings)


async def get_organization_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    organization_repository: Annotated[
        OrganizationRepository,
        Depends(get_organization_repository),
    ],
    membership_repository: Annotated[
        MembershipRepository,
        Depends(get_membership_repository),
    ],
    profile_repository: Annotated[
        OrganizationProfileRepository,
        Depends(get_organization_profile_repository),
    ],
    plan_repository: Annotated[
        OrganizationPlanRepository,
        Depends(get_organization_plan_repository),
    ],
    storage: Annotated[
        OrganizationAssetsStorage,
        Depends(get_organization_storage),
    ],
) -> OrganizationService:
    return OrganizationService(
        session=session,
        organization_repository=organization_repository,
        membership_repository=membership_repository,
        profile_repository=profile_repository,
        plan_repository=plan_repository,
        storage=storage,
    )
