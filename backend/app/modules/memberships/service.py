from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import OrganizationRole, parse_organization_role
from app.core.config import Settings
from app.modules.memberships.exceptions import (
    AlreadyOrganizationMemberError,
    InvalidMembershipOperationError,
    InvitationAlreadyAcceptedError,
    InvitationEmailMismatchError,
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationNotPendingError,
    InvitationRevokedError,
    LastOwnerInvariantError,
    MembershipNotFoundError,
    PendingInvitationExistsError,
)
from app.modules.memberships.models import OrganizationInvitation, OrganizationMembership
from app.modules.memberships.repository import InvitationRepository, MembershipRepository
from app.modules.memberships.schemas import OrganizationMemberResponse
from app.modules.memberships.tokens import generate_invitation_token, hash_invitation_token
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.shared.email import normalize_email

_LAST_OWNER_MESSAGE = (
    "Organization must always have at least one owner. "
    "Transfer ownership or promote another member first."
)


class MembershipService:
    def __init__(
        self,
        session: AsyncSession,
        membership_repository: MembershipRepository,
        invitation_repository: InvitationRepository,
        user_repository: UserRepository,
        settings: Settings,
    ) -> None:
        self._session = session
        self._membership_repository = membership_repository
        self._invitation_repository = invitation_repository
        self._user_repository = user_repository
        self._settings = settings

    async def list_members(
        self,
        organization_id: UUID,
    ) -> list[OrganizationMemberResponse]:
        rows = await self._membership_repository.list_members_for_organization(
            organization_id,
        )
        return [
            OrganizationMemberResponse(
                id=membership.id,
                user_id=member_user.id,
                display_name=member_user.display_name,
                email=member_user.email,
                role=membership.role,
                created_at=membership.created_at,
            )
            for membership, member_user in rows
        ]

    async def list_pending_invitations(
        self,
        organization_id: UUID,
    ) -> list[OrganizationInvitation]:
        return await self._invitation_repository.list_pending_for_organization(
            organization_id,
        )

    async def create_invitation(
        self,
        organization_id: UUID,
        user: User,
        email: str,
    ) -> tuple[OrganizationInvitation, str | None]:
        normalized_email = normalize_email(email)

        existing_user = await self._user_repository.get_by_email(normalized_email)
        if existing_user is not None:
            membership = await self._membership_repository.get_by_organization_and_user(
                organization_id,
                existing_user.id,
            )
            if membership is not None:
                raise AlreadyOrganizationMemberError(
                    "User is already a member of this organization",
                )

        pending = await self._invitation_repository.get_pending_by_organization_and_email(
            organization_id,
            normalized_email,
        )
        if pending is not None:
            raise PendingInvitationExistsError(
                "A pending invitation already exists for this email",
            )

        raw_token = generate_invitation_token()
        token_hash = hash_invitation_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self._settings.invitation_expiry_days,
        )

        invitation = OrganizationInvitation(
            organization_id=organization_id,
            email=normalized_email,
            role=OrganizationRole.MEMBER.value,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by_user_id=user.id,
        )
        invitation = await self._invitation_repository.create(invitation)
        await self._session.commit()
        await self._session.refresh(invitation)

        invite_url: str | None = None
        if self._settings.app_env == "development":
            base = self._settings.frontend_app_url.rstrip("/")
            invite_url = f"{base}/invitations/accept?token={raw_token}"

        return invitation, invite_url

    async def revoke_invitation(
        self,
        organization_id: UUID,
        invitation_id: UUID,
    ) -> OrganizationInvitation:
        invitation = await self._invitation_repository.get_by_id_and_organization(
            invitation_id,
            organization_id,
        )
        if invitation is None:
            raise InvitationNotFoundError("Invitation not found")

        now = datetime.now(timezone.utc)
        if (
            invitation.accepted_at is not None
            or invitation.revoked_at is not None
            or invitation.expires_at <= now
        ):
            raise InvitationNotPendingError("Only pending invitations can be revoked")

        invitation.revoked_at = now
        await self._session.commit()
        await self._session.refresh(invitation)
        return invitation

    async def accept_invitation(
        self,
        user: User,
        raw_token: str,
    ) -> OrganizationInvitation:
        token_hash = hash_invitation_token(raw_token)
        invitation = await self._invitation_repository.get_by_token_hash(token_hash)
        if invitation is None:
            raise InvitationNotFoundError("Invitation not found")

        if invitation.revoked_at is not None:
            raise InvitationRevokedError("Invitation has been revoked")

        if normalize_email(user.email) != normalize_email(invitation.email):
            raise InvitationEmailMismatchError(
                "Invitation email does not match the authenticated user",
            )

        existing = await self._membership_repository.get_by_organization_and_user(
            invitation.organization_id,
            user.id,
        )

        if invitation.accepted_at is not None:
            if existing is not None:
                return invitation
            raise InvitationAlreadyAcceptedError("Invitation has already been accepted")

        now = datetime.now(timezone.utc)
        if invitation.expires_at <= now:
            raise InvitationExpiredError("Invitation has expired")

        if existing is not None:
            invitation.accepted_at = now
            await self._session.commit()
            await self._session.refresh(invitation)
            return invitation

        try:
            await self._membership_repository.create_member_membership(
                organization_id=invitation.organization_id,
                user_id=user.id,
            )
            invitation.accepted_at = now
            await self._session.commit()
            await self._session.refresh(invitation)
            return invitation
        except IntegrityError:
            await self._session.rollback()
            membership = await self._membership_repository.get_by_organization_and_user(
                invitation.organization_id,
                user.id,
            )
            if membership is None:
                raise
            invitation = await self._invitation_repository.get_by_token_hash(token_hash)
            if invitation is None:
                raise InvitationNotFoundError("Invitation not found")
            if invitation.accepted_at is None:
                invitation.accepted_at = datetime.now(timezone.utc)
                await self._session.commit()
                await self._session.refresh(invitation)
            return invitation
        except Exception:
            await self._session.rollback()
            raise

    async def update_member_role(
        self,
        *,
        organization_id: UUID,
        membership_id: UUID,
        new_role: OrganizationRole,
    ) -> OrganizationMembership:
        try:
            owners = await self._membership_repository.lock_owner_memberships(
                organization_id,
            )
            membership = await self._membership_repository.get_by_id_and_organization_for_update(
                membership_id,
                organization_id,
            )
            if membership is None:
                raise MembershipNotFoundError("Membership not found")

            current_role = parse_organization_role(membership.role)
            if current_role == new_role:
                await self._session.commit()
                await self._session.refresh(membership)
                return membership

            if (
                current_role == OrganizationRole.OWNER
                and new_role == OrganizationRole.MEMBER
            ):
                self._ensure_another_owner_remains(
                    owners=owners,
                    membership_id=membership.id,
                )

            membership.role = new_role.value
            await self._session.flush()
            await self._session.commit()
            await self._session.refresh(membership)
            return membership
        except Exception:
            await self._session.rollback()
            raise

    async def remove_member(
        self,
        *,
        organization_id: UUID,
        membership_id: UUID,
    ) -> None:
        try:
            owners = await self._membership_repository.lock_owner_memberships(
                organization_id,
            )
            membership = await self._membership_repository.get_by_id_and_organization_for_update(
                membership_id,
                organization_id,
            )
            if membership is None:
                raise MembershipNotFoundError("Membership not found")

            if parse_organization_role(membership.role) == OrganizationRole.OWNER:
                self._ensure_another_owner_remains(
                    owners=owners,
                    membership_id=membership.id,
                )

            await self._membership_repository.delete(membership)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def leave_organization(
        self,
        *,
        organization_id: UUID,
        user: User,
    ) -> None:
        try:
            owners = await self._membership_repository.lock_owner_memberships(
                organization_id,
            )
            membership = (
                await self._membership_repository.get_by_organization_and_user_for_update(
                    organization_id,
                    user.id,
                )
            )
            if membership is None:
                raise MembershipNotFoundError("Membership not found")

            if parse_organization_role(membership.role) == OrganizationRole.OWNER:
                self._ensure_another_owner_remains(
                    owners=owners,
                    membership_id=membership.id,
                )

            await self._membership_repository.delete(membership)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def transfer_ownership(
        self,
        *,
        organization_id: UUID,
        current_user: User,
        target_membership_id: UUID,
    ) -> None:
        try:
            await self._membership_repository.lock_owner_memberships(organization_id)

            source = (
                await self._membership_repository.get_by_organization_and_user_for_update(
                    organization_id,
                    current_user.id,
                )
            )
            if source is None:
                raise MembershipNotFoundError("Membership not found")

            if parse_organization_role(source.role) != OrganizationRole.OWNER:
                raise InvalidMembershipOperationError(
                    "Only an organization owner can transfer ownership",
                )

            if source.id == target_membership_id:
                raise InvalidMembershipOperationError(
                    "Cannot transfer ownership to yourself",
                )

            target = await self._membership_repository.get_by_id_and_organization_for_update(
                target_membership_id,
                organization_id,
            )
            if target is None:
                raise MembershipNotFoundError("Membership not found")

            target.role = OrganizationRole.OWNER.value
            source.role = OrganizationRole.MEMBER.value
            await self._session.flush()
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    @staticmethod
    def _ensure_another_owner_remains(
        *,
        owners: list[OrganizationMembership],
        membership_id: UUID,
    ) -> None:
        remaining_owners = [owner for owner in owners if owner.id != membership_id]
        if not remaining_owners:
            raise LastOwnerInvariantError(_LAST_OWNER_MESSAGE)
