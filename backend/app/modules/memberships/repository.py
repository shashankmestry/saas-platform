from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import OrganizationRole
from app.modules.memberships.models import OrganizationInvitation, OrganizationMembership
from app.modules.users.models import User


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        membership: OrganizationMembership,
    ) -> OrganizationMembership:
        self._session.add(membership)
        await self._session.flush()
        await self._session.refresh(membership)
        return membership

    async def create_owner_membership(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> OrganizationMembership:
        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user_id,
            role=OrganizationRole.OWNER.value,
        )
        return await self.create(membership)

    async def create_member_membership(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> OrganizationMembership:
        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user_id,
            role=OrganizationRole.MEMBER.value,
        )
        return await self.create(membership)

    async def get_by_organization_and_user(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> OrganizationMembership | None:
        statement = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id_and_organization(
        self,
        membership_id: UUID,
        organization_id: UUID,
    ) -> OrganizationMembership | None:
        statement = select(OrganizationMembership).where(
            OrganizationMembership.id == membership_id,
            OrganizationMembership.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id_and_organization_for_update(
        self,
        membership_id: UUID,
        organization_id: UUID,
    ) -> OrganizationMembership | None:
        statement = (
            select(OrganizationMembership)
            .where(
                OrganizationMembership.id == membership_id,
                OrganizationMembership.organization_id == organization_id,
            )
            .with_for_update()
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_organization_and_user_for_update(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> OrganizationMembership | None:
        statement = (
            select(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == user_id,
            )
            .with_for_update()
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def lock_owner_memberships(
        self,
        organization_id: UUID,
    ) -> list[OrganizationMembership]:
        """Lock all owner memberships for an organization (FOR UPDATE)."""
        statement = (
            select(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.role == OrganizationRole.OWNER.value,
            )
            .order_by(OrganizationMembership.id.asc())
            .with_for_update()
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count_owners(self, organization_id: UUID) -> int:
        statement = select(func.count()).select_from(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.role == OrganizationRole.OWNER.value,
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def count_members(self, organization_id: UUID) -> int:
        statement = select(func.count()).select_from(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def list_members_for_organization(
        self,
        organization_id: UUID,
    ) -> list[tuple[OrganizationMembership, User]]:
        statement = (
            select(OrganizationMembership, User)
            .join(User, User.id == OrganizationMembership.user_id)
            .where(OrganizationMembership.organization_id == organization_id)
            .order_by(OrganizationMembership.created_at.asc())
        )
        result = await self._session.execute(statement)
        return list(result.all())

    async def delete(self, membership: OrganizationMembership) -> None:
        await self._session.delete(membership)
        await self._session.flush()


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        invitation: OrganizationInvitation,
    ) -> OrganizationInvitation:
        self._session.add(invitation)
        await self._session.flush()
        await self._session.refresh(invitation)
        return invitation

    async def get_by_id_and_organization(
        self,
        invitation_id: UUID,
        organization_id: UUID,
    ) -> OrganizationInvitation | None:
        statement = select(OrganizationInvitation).where(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> OrganizationInvitation | None:
        statement = select(OrganizationInvitation).where(
            OrganizationInvitation.token_hash == token_hash,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_pending_by_organization_and_email(
        self,
        organization_id: UUID,
        email: str,
    ) -> OrganizationInvitation | None:
        now = datetime.now(timezone.utc)
        statement = select(OrganizationInvitation).where(
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.email == email,
            OrganizationInvitation.accepted_at.is_(None),
            OrganizationInvitation.revoked_at.is_(None),
            OrganizationInvitation.expires_at > now,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_pending_for_organization(
        self,
        organization_id: UUID,
    ) -> list[OrganizationInvitation]:
        now = datetime.now(timezone.utc)
        statement = (
            select(OrganizationInvitation)
            .where(
                OrganizationInvitation.organization_id == organization_id,
                OrganizationInvitation.accepted_at.is_(None),
                OrganizationInvitation.revoked_at.is_(None),
                OrganizationInvitation.expires_at > now,
            )
            .order_by(OrganizationInvitation.created_at.desc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count_pending(self, organization_id: UUID) -> int:
        now = datetime.now(timezone.utc)
        statement = select(func.count()).select_from(OrganizationInvitation).where(
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.accepted_at.is_(None),
            OrganizationInvitation.revoked_at.is_(None),
            OrganizationInvitation.expires_at > now,
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())
