from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memberships.models import OrganizationMembership
from app.modules.organizations.models import Organization, OrganizationProfile


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, organization: Organization) -> Organization:
        self._session.add(organization)
        await self._session.flush()
        await self._session.refresh(organization)
        return organization

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        statement = select(Organization).where(Organization.id == organization_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Organization | None:
        statement = select(Organization).where(Organization.slug == slug)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: UUID) -> list[Organization]:
        statement = (
            select(Organization)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Organization.id,
            )
            .where(OrganizationMembership.user_id == user_id)
            .order_by(Organization.created_at.asc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def list_with_membership_for_user(
        self,
        user_id: UUID,
    ) -> list[tuple[Organization, OrganizationMembership]]:
        statement = (
            select(Organization, OrganizationMembership)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Organization.id,
            )
            .where(OrganizationMembership.user_id == user_id)
            .order_by(Organization.created_at.asc())
        )
        result = await self._session.execute(statement)
        return list(result.all())


class OrganizationProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_organization_id(
        self,
        organization_id: UUID,
    ) -> OrganizationProfile | None:
        statement = select(OrganizationProfile).where(
            OrganizationProfile.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, profile: OrganizationProfile) -> OrganizationProfile:
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return profile
