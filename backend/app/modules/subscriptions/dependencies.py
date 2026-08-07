from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.plans.repository import OrganizationPlanRepository
from app.modules.subscriptions.repository import OrganizationSubscriptionRepository
from app.modules.subscriptions.service import SubscriptionService


async def get_organization_subscription_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrganizationSubscriptionRepository:
    return OrganizationSubscriptionRepository(session)


async def get_organization_plan_repository_for_subscriptions(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrganizationPlanRepository:
    return OrganizationPlanRepository(session)


async def get_subscription_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    subscription_repository: Annotated[
        OrganizationSubscriptionRepository,
        Depends(get_organization_subscription_repository),
    ],
    plan_repository: Annotated[
        OrganizationPlanRepository,
        Depends(get_organization_plan_repository_for_subscriptions),
    ],
) -> SubscriptionService:
    return SubscriptionService(
        session=session,
        subscription_repository=subscription_repository,
        plan_repository=plan_repository,
    )
