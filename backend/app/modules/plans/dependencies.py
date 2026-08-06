from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.memberships.repository import InvitationRepository, MembershipRepository
from app.modules.plans.repository import OrganizationPlanRepository
from app.modules.plans.service import PlanService


async def get_organization_plan_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrganizationPlanRepository:
    return OrganizationPlanRepository(session)


async def get_membership_repository_for_plans(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MembershipRepository:
    return MembershipRepository(session)


async def get_invitation_repository_for_plans(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvitationRepository:
    return InvitationRepository(session)


async def get_plan_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    plan_repository: Annotated[
        OrganizationPlanRepository,
        Depends(get_organization_plan_repository),
    ],
    membership_repository: Annotated[
        MembershipRepository,
        Depends(get_membership_repository_for_plans),
    ],
    invitation_repository: Annotated[
        InvitationRepository,
        Depends(get_invitation_repository_for_plans),
    ],
) -> PlanService:
    return PlanService(
        session=session,
        plan_repository=plan_repository,
        membership_repository=membership_repository,
        invitation_repository=invitation_repository,
    )
