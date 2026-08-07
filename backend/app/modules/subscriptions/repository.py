from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.subscriptions.models import OrganizationSubscription


class OrganizationSubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        subscription: OrganizationSubscription,
    ) -> OrganizationSubscription:
        self._session.add(subscription)
        await self._session.flush()
        await self._session.refresh(subscription)
        return subscription

    async def get_by_organization_id(
        self,
        organization_id: UUID,
    ) -> OrganizationSubscription | None:
        statement = select(OrganizationSubscription).where(
            OrganizationSubscription.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_organization_id_for_update(
        self,
        organization_id: UUID,
    ) -> OrganizationSubscription | None:
        statement = (
            select(OrganizationSubscription)
            .where(OrganizationSubscription.organization_id == organization_id)
            .with_for_update()
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
