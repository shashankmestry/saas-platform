from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.plans.models import OrganizationPlan


class OrganizationPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, organization_plan: OrganizationPlan) -> OrganizationPlan:
        self._session.add(organization_plan)
        await self._session.flush()
        await self._session.refresh(organization_plan)
        return organization_plan

    async def get_by_organization_id(
        self,
        organization_id: UUID,
    ) -> OrganizationPlan | None:
        statement = select(OrganizationPlan).where(
            OrganizationPlan.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_organization_id_for_update(
        self,
        organization_id: UUID,
    ) -> OrganizationPlan | None:
        """Lock the organization plan row (FOR UPDATE) for seat-limit serialization."""
        statement = (
            select(OrganizationPlan)
            .where(OrganizationPlan.organization_id == organization_id)
            .with_for_update()
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
