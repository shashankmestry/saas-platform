import re
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import OrganizationRole, permissions_for_role
from app.core.storage import (
    ALLOWED_LOGO_CONTENT_TYPES,
    MAX_LOGO_BYTES,
    OrganizationAssetsStorage,
    StorageError,
)
from app.modules.memberships.context import OrganizationContext
from app.modules.memberships.repository import MembershipRepository
from app.modules.organizations.exceptions import (
    LogoObjectMissingError,
    LogoStorageOperationError,
    LogoValidationError,
    OrganizationSlugConflictError,
)
from app.modules.organizations.models import Organization, OrganizationProfile
from app.modules.organizations.repository import (
    OrganizationProfileRepository,
    OrganizationRepository,
)
from app.modules.organizations.schemas import (
    LogoConfirmRequest,
    LogoUploadRequest,
    LogoUploadResponse,
    OrganizationProfileResponse,
    OrganizationProfileUpdate,
    OrganizationResponse,
)
from app.modules.users.models import User


def slugify_organization_name(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "organization"


class OrganizationService:
    def __init__(
        self,
        session: AsyncSession,
        organization_repository: OrganizationRepository,
        membership_repository: MembershipRepository,
        profile_repository: OrganizationProfileRepository,
        storage: OrganizationAssetsStorage,
    ) -> None:
        self._session = session
        self._organization_repository = organization_repository
        self._membership_repository = membership_repository
        self._profile_repository = profile_repository
        self._storage = storage

    async def list_for_user(self, user: User) -> list[OrganizationResponse]:
        rows = await self._organization_repository.list_with_membership_for_user(user.id)
        responses: list[OrganizationResponse] = []
        for organization, membership in rows:
            context = OrganizationContext.from_membership(
                user=user,
                organization=organization,
                membership=membership,
            )
            responses.append(
                OrganizationResponse(
                    id=organization.id,
                    name=organization.name,
                    slug=organization.slug,
                    created_at=organization.created_at,
                    updated_at=organization.updated_at,
                    role=context.role.value,
                    permissions=context.permission_values(),
                )
            )
        return responses

    async def create_organization(self, user: User, name: str) -> OrganizationResponse:
        base_slug = slugify_organization_name(name)
        cleaned_name = name.strip()

        for _ in range(5):
            slug = await self._generate_unique_slug(base_slug)
            try:
                organization = Organization(name=cleaned_name, slug=slug)
                organization = await self._organization_repository.create(organization)
                membership = await self._membership_repository.create_owner_membership(
                    organization_id=organization.id,
                    user_id=user.id,
                )
                await self._session.commit()
                await self._session.refresh(organization)
                await self._session.refresh(membership)

                role = OrganizationRole.OWNER
                return OrganizationResponse(
                    id=organization.id,
                    name=organization.name,
                    slug=organization.slug,
                    created_at=organization.created_at,
                    updated_at=organization.updated_at,
                    role=role.value,
                    permissions=sorted(
                        permission.value for permission in permissions_for_role(role)
                    ),
                )
            except IntegrityError:
                await self._session.rollback()
                continue

        raise OrganizationSlugConflictError(
            "Unable to generate a unique organization slug",
        )

    async def get_profile(
        self,
        organization: Organization,
    ) -> OrganizationProfileResponse:
        profile = await self._profile_repository.get_by_organization_id(organization.id)
        return await self._to_profile_response(organization, profile)

    async def update_profile(
        self,
        *,
        organization_id: UUID,
        payload: OrganizationProfileUpdate,
    ) -> OrganizationProfileResponse:
        try:
            organization = await self._organization_repository.get_by_id(organization_id)
            if organization is None:
                raise ValueError("Organization not found")

            updates = payload.model_dump(exclude_unset=True)
            if "name" in updates:
                organization.name = updates.pop("name")

            profile = await self._profile_repository.get_by_organization_id(organization_id)
            profile_updates = updates

            if profile is None:
                if profile_updates:
                    profile = OrganizationProfile(
                        organization_id=organization_id,
                        **profile_updates,
                    )
                    profile = await self._profile_repository.create(profile)
            elif profile_updates:
                for key, value in profile_updates.items():
                    setattr(profile, key, value)
                await self._session.flush()
                await self._session.refresh(profile)

            await self._session.commit()
            await self._session.refresh(organization)
            if profile is not None:
                await self._session.refresh(profile)

            return await self._to_profile_response(organization, profile)
        except Exception:
            await self._session.rollback()
            raise

    async def request_logo_upload(
        self,
        *,
        organization_id: UUID,
        payload: LogoUploadRequest,
    ) -> LogoUploadResponse:
        if payload.content_type not in ALLOWED_LOGO_CONTENT_TYPES:
            raise LogoValidationError("Unsupported logo content type")
        if payload.file_size > MAX_LOGO_BYTES:
            raise LogoValidationError("Logo file exceeds the 2 MB limit")

        path = self._storage.build_logo_path(organization_id, payload.content_type)
        try:
            authorization = await self._storage.create_signed_upload(path)
        except StorageError as exc:
            raise LogoStorageOperationError(str(exc)) from exc

        return LogoUploadResponse(
            bucket=authorization.bucket,
            path=authorization.path,
            token=authorization.token,
            signed_url=authorization.signed_url,
        )

    async def confirm_logo_upload(
        self,
        *,
        organization_id: UUID,
        payload: LogoConfirmRequest,
    ) -> OrganizationProfileResponse:
        path = payload.path
        if not self._storage.is_valid_logo_path_for_organization(organization_id, path):
            raise LogoValidationError("Invalid logo storage path")

        try:
            object_info = await self._storage.get_object_info(path)
        except StorageError as exc:
            raise LogoStorageOperationError(str(exc)) from exc

        if object_info is None:
            raise LogoObjectMissingError("Uploaded logo object was not found")

        if (
            object_info.content_type is not None
            and object_info.content_type.lower() not in ALLOWED_LOGO_CONTENT_TYPES
        ):
            raise LogoValidationError("Uploaded logo has an unsupported content type")

        if object_info.size is not None and object_info.size > MAX_LOGO_BYTES:
            raise LogoValidationError("Uploaded logo exceeds the 2 MB limit")

        old_path: str | None = None
        try:
            organization = await self._organization_repository.get_by_id(organization_id)
            if organization is None:
                raise ValueError("Organization not found")

            profile = await self._profile_repository.get_by_organization_id(organization_id)
            if profile is None:
                profile = OrganizationProfile(
                    organization_id=organization_id,
                    logo_path=path,
                )
                profile = await self._profile_repository.create(profile)
            else:
                old_path = profile.logo_path
                profile.logo_path = path
                await self._session.flush()
                await self._session.refresh(profile)

            await self._session.commit()
            await self._session.refresh(organization)
            await self._session.refresh(profile)
        except Exception:
            await self._session.rollback()
            raise

        if old_path and old_path != path:
            try:
                await self._storage.delete_object(old_path)
            except StorageError:
                # Non-authoritative cleanup; new logo already committed.
                pass

        return await self._to_profile_response(organization, profile)

    async def delete_logo(
        self,
        *,
        organization_id: UUID,
    ) -> OrganizationProfileResponse:
        path_to_delete: str | None = None
        try:
            organization = await self._organization_repository.get_by_id(organization_id)
            if organization is None:
                raise ValueError("Organization not found")

            profile = await self._profile_repository.get_by_organization_id(organization_id)
            if profile is None or not profile.logo_path:
                return await self._to_profile_response(organization, profile)

            path_to_delete = profile.logo_path
            profile.logo_path = None
            await self._session.flush()
            await self._session.refresh(profile)
            await self._session.commit()
            await self._session.refresh(organization)
            await self._session.refresh(profile)
        except Exception:
            await self._session.rollback()
            raise

        if path_to_delete:
            try:
                await self._storage.delete_object(path_to_delete)
            except StorageError:
                pass

        return await self._to_profile_response(organization, profile)

    async def _to_profile_response(
        self,
        organization: Organization,
        profile: OrganizationProfile | None,
    ) -> OrganizationProfileResponse:
        logo_url: str | None = None
        if profile and profile.logo_path:
            logo_url = await self._storage.create_signed_read_url(profile.logo_path)

        return OrganizationProfileResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            website=profile.website if profile else None,
            contact_email=profile.contact_email if profile else None,
            phone=profile.phone if profile else None,
            country_code=profile.country_code if profile else None,
            timezone=profile.timezone if profile else None,
            default_currency=profile.default_currency if profile else None,
            logo_url=logo_url,
        )

    async def _generate_unique_slug(self, base_slug: str) -> str:
        candidate = base_slug
        suffix = 2

        while suffix <= 100:
            existing = await self._organization_repository.get_by_slug(candidate)
            if existing is None:
                return candidate
            candidate = f"{base_slug}-{suffix}"
            suffix += 1

        raise OrganizationSlugConflictError(
            "Unable to generate a unique organization slug",
        )
