"""Organization logo upload/confirm/delete tests."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient

from app.core.authorization import OrganizationPermission, OrganizationRole
from app.core.storage import (
    MAX_LOGO_BYTES,
    OrganizationAssetsStorage,
    SignedUploadAuthorization,
    StoredObjectInfo,
)
from app.modules.auth.dependencies import get_current_user
from app.modules.memberships.authorization import require_organization_permission
from app.modules.memberships.context import OrganizationContext
from app.modules.organizations.dependencies import get_organization_service
from app.modules.organizations.exceptions import (
    LogoObjectMissingError,
    LogoValidationError,
)
from app.modules.organizations.models import Organization, OrganizationProfile
from app.modules.organizations.router import router as organizations_router
from app.modules.organizations.schemas import (
    LogoConfirmRequest,
    LogoUploadRequest,
)
from app.modules.organizations.service import OrganizationService


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _organization(*, organization_id=None) -> Organization:
    return Organization(
        id=organization_id or uuid4(),
        name="Acme",
        slug="acme",
        created_at=_now(),
        updated_at=_now(),
    )


class FakeOrganizationRepository:
    def __init__(self, organizations: list[Organization]) -> None:
        self.organizations = organizations

    async def get_by_id(self, organization_id):
        for organization in self.organizations:
            if organization.id == organization_id:
                return organization
        return None


class FakeProfileRepository:
    def __init__(self, profiles: list[OrganizationProfile] | None = None) -> None:
        self.profiles = profiles or []
        self.create_calls = 0

    async def get_by_organization_id(self, organization_id):
        for profile in self.profiles:
            if profile.organization_id == organization_id:
                return profile
        return None

    async def create(self, profile: OrganizationProfile) -> OrganizationProfile:
        self.create_calls += 1
        if profile.id is None:
            profile.id = uuid4()
        profile.created_at = _now()
        profile.updated_at = _now()
        self.profiles.append(profile)
        return profile


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def refresh(self, _obj) -> None:
        return None


class FakeStorage:
    def __init__(self, *, bucket: str = "organization-assets") -> None:
        self.bucket = bucket
        self.objects: dict[str, StoredObjectInfo] = {}
        self.deleted_paths: list[str] = []
        self.upload_authorizations: list[str] = []
        self.signed_reads: list[str] = []
        self._real = OrganizationAssetsStorage(
            client=SimpleNamespace(),
            settings=SimpleNamespace(
                organization_assets_bucket=bucket,
                logo_signed_url_ttl_seconds=900,
            ),
        )

    def build_logo_path(self, organization_id, content_type: str) -> str:
        return self._real.build_logo_path(organization_id, content_type)

    def is_valid_logo_path_for_organization(self, organization_id, path: str) -> bool:
        return self._real.is_valid_logo_path_for_organization(organization_id, path)

    async def create_signed_upload(self, path: str) -> SignedUploadAuthorization:
        self.upload_authorizations.append(path)
        return SignedUploadAuthorization(
            bucket=self.bucket,
            path=path,
            token="upload-token",
            signed_url=f"https://example.test/upload/{path}?token=upload-token",
        )

    async def get_object_info(self, path: str) -> StoredObjectInfo | None:
        return self.objects.get(path)

    async def create_signed_read_url(self, path: str) -> str | None:
        self.signed_reads.append(path)
        if path not in self.objects and not path:
            return None
        return f"https://example.test/read/{path}?sig=temp"

    async def delete_object(self, path: str) -> None:
        self.deleted_paths.append(path)
        self.objects.pop(path, None)


def _service(
    organization: Organization,
    *,
    profiles: list[OrganizationProfile] | None = None,
    storage: FakeStorage | None = None,
) -> tuple[OrganizationService, FakeProfileRepository, FakeSession, FakeStorage]:
    session = FakeSession()
    profile_repository = FakeProfileRepository(profiles)
    fake_storage = storage or FakeStorage()
    service = OrganizationService(
        session=session,
        organization_repository=FakeOrganizationRepository([organization]),
        membership_repository=SimpleNamespace(),
        profile_repository=profile_repository,
        storage=fake_storage,
    )
    return service, profile_repository, session, fake_storage


def _make_context(*, user, organization, role: OrganizationRole) -> OrganizationContext:
    membership = SimpleNamespace(
        id=uuid4(),
        organization_id=organization.id,
        user_id=user.id,
        role=role.value,
        created_at=_now(),
    )
    return OrganizationContext.from_membership(
        user=user,
        organization=organization,
        membership=membership,
    )


class FakeOrganizationService:
    def __init__(self, organization: Organization) -> None:
        self.organization = organization
        self.logo_path: str | None = None
        self.upload_calls: list = []
        self.confirm_calls: list = []
        self.delete_calls: list = []

    async def get_profile(self, organization: Organization):
        return {
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug,
            "website": None,
            "contact_email": None,
            "phone": None,
            "country_code": None,
            "timezone": None,
            "default_currency": None,
            "logo_url": (
                f"https://example.test/read/{self.logo_path}?sig=temp"
                if self.logo_path
                else None
            ),
        }

    async def request_logo_upload(self, *, organization_id, payload: LogoUploadRequest):
        self.upload_calls.append((organization_id, payload))
        path = f"organizations/{organization_id}/logo/{uuid4().hex}.png"
        return {
            "bucket": "organization-assets",
            "path": path,
            "token": "token",
            "signed_url": f"https://example.test/upload/{path}",
        }

    async def confirm_logo_upload(self, *, organization_id, payload: LogoConfirmRequest):
        self.confirm_calls.append((organization_id, payload))
        self.logo_path = payload.path
        return await self.get_profile(self.organization)

    async def delete_logo(self, *, organization_id):
        self.delete_calls.append(organization_id)
        self.logo_path = None
        return await self.get_profile(self.organization)


def _build_app(*, current_user, role: OrganizationRole | None, organization):
    app = FastAPI()
    app.include_router(organizations_router, prefix="/organizations")
    service = FakeOrganizationService(organization)

    async def override_current_user():
        return current_user

    async def override_organization_service():
        return service

    permission_allowed = {
        OrganizationPermission.ORGANIZATION_VIEW: role
        in {OrganizationRole.OWNER, OrganizationRole.MEMBER},
        OrganizationPermission.ORGANIZATION_MANAGE: role == OrganizationRole.OWNER,
    }

    for permission, allowed in permission_allowed.items():

        def make_override(
            is_allowed: bool = allowed,
            current_role: OrganizationRole | None = role,
        ):
            async def dependency(organization_id):
                if current_role is None or not is_allowed:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Forbidden",
                    )
                if str(organization_id) != str(organization.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Forbidden",
                    )
                return _make_context(
                    user=current_user,
                    organization=organization,
                    role=current_role,
                )

            return dependency

        app.dependency_overrides[require_organization_permission(permission)] = (
            make_override()
        )

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_organization_service] = override_organization_service
    return app, service


@pytest.mark.asyncio
async def test_member_can_view_logo_through_profile():
    organization = _organization()
    user = SimpleNamespace(id=uuid4(), email="member@example.com")
    app, service = _build_app(
        current_user=user,
        role=OrganizationRole.MEMBER,
        organization=organization,
    )
    service.logo_path = f"organizations/{organization.id}/logo/{uuid4().hex}.png"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/organizations/{organization.id}/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["logo_url"].startswith("https://example.test/read/")
    assert "logo_path" not in body


@pytest.mark.asyncio
async def test_member_cannot_request_logo_upload():
    organization = _organization()
    user = SimpleNamespace(id=uuid4(), email="member@example.com")
    app, service = _build_app(
        current_user=user,
        role=OrganizationRole.MEMBER,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/organizations/{organization.id}/logo/upload",
            json={"content_type": "image/png", "file_size": 1024},
        )

    assert response.status_code == 403
    assert service.upload_calls == []


@pytest.mark.asyncio
async def test_owner_can_request_upload_authorization():
    organization = _organization()
    user = SimpleNamespace(id=uuid4(), email="owner@example.com")
    app, service = _build_app(
        current_user=user,
        role=OrganizationRole.OWNER,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/organizations/{organization.id}/logo/upload",
            json={"content_type": "image/png", "file_size": 1024},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["bucket"] == "organization-assets"
    assert body["path"].startswith(f"organizations/{organization.id}/logo/")
    assert body["token"]
    assert len(service.upload_calls) == 1


@pytest.mark.asyncio
async def test_unsupported_content_type_rejected():
    organization = _organization()
    service, _, _, _ = _service(organization)

    with pytest.raises(LogoValidationError, match="Unsupported"):
        await service.request_logo_upload(
            organization_id=organization.id,
            payload=LogoUploadRequest(content_type="image/svg+xml", file_size=100),
        )


@pytest.mark.asyncio
async def test_file_too_large_rejected():
    organization = _organization()
    service, _, _, _ = _service(organization)

    with pytest.raises(LogoValidationError, match="2 MB"):
        await service.request_logo_upload(
            organization_id=organization.id,
            payload=LogoUploadRequest(
                content_type="image/png",
                file_size=MAX_LOGO_BYTES + 1,
            ),
        )


@pytest.mark.asyncio
async def test_generated_path_belongs_to_organization():
    organization = _organization()
    service, profile_repository, session, storage = _service(organization)

    response = await service.request_logo_upload(
        organization_id=organization.id,
        payload=LogoUploadRequest(content_type="image/webp", file_size=2048),
    )

    assert response.path.startswith(f"organizations/{organization.id}/logo/")
    assert response.path.endswith(".webp")
    assert storage.upload_authorizations == [response.path]
    assert profile_repository.create_calls == 0
    assert session.committed is False


@pytest.mark.asyncio
async def test_upload_authorization_does_not_update_logo_path():
    organization = _organization()
    existing = OrganizationProfile(
        id=uuid4(),
        organization_id=organization.id,
        logo_path=None,
        created_at=_now(),
        updated_at=_now(),
    )
    service, _, session, _ = _service(organization, profiles=[existing])

    await service.request_logo_upload(
        organization_id=organization.id,
        payload=LogoUploadRequest(content_type="image/png", file_size=100),
    )

    assert existing.logo_path is None
    assert session.committed is False


@pytest.mark.asyncio
async def test_valid_confirm_updates_logo_path():
    organization = _organization()
    storage = FakeStorage()
    path = storage.build_logo_path(organization.id, "image/png")
    storage.objects[path] = StoredObjectInfo(
        path=path,
        content_type="image/png",
        size=1024,
    )
    service, profile_repository, session, _ = _service(organization, storage=storage)

    response = await service.confirm_logo_upload(
        organization_id=organization.id,
        payload=LogoConfirmRequest(path=path),
    )

    assert profile_repository.create_calls == 1
    assert profile_repository.profiles[0].logo_path == path
    assert session.committed is True
    assert response.logo_url is not None
    assert path in response.logo_url


@pytest.mark.asyncio
async def test_arbitrary_path_cannot_be_confirmed():
    organization = _organization()
    service, _, _, _ = _service(organization)

    with pytest.raises(LogoValidationError, match="Invalid logo storage path"):
        await service.confirm_logo_upload(
            organization_id=organization.id,
            payload=LogoConfirmRequest(path="evil/path.png"),
        )


@pytest.mark.asyncio
async def test_another_organization_path_cannot_be_confirmed():
    organization = _organization()
    other_id = uuid4()
    storage = FakeStorage()
    foreign_path = storage.build_logo_path(other_id, "image/png")
    storage.objects[foreign_path] = StoredObjectInfo(
        path=foreign_path,
        content_type="image/png",
        size=100,
    )
    service, _, _, _ = _service(organization, storage=storage)

    with pytest.raises(LogoValidationError, match="Invalid logo storage path"):
        await service.confirm_logo_upload(
            organization_id=organization.id,
            payload=LogoConfirmRequest(path=foreign_path),
        )


@pytest.mark.asyncio
async def test_missing_storage_object_cannot_be_confirmed():
    organization = _organization()
    storage = FakeStorage()
    path = storage.build_logo_path(organization.id, "image/png")
    service, _, _, _ = _service(organization, storage=storage)

    with pytest.raises(LogoObjectMissingError):
        await service.confirm_logo_upload(
            organization_id=organization.id,
            payload=LogoConfirmRequest(path=path),
        )


@pytest.mark.asyncio
async def test_replace_logo_updates_after_verification_and_cleans_old():
    organization = _organization()
    storage = FakeStorage()
    old_path = storage.build_logo_path(organization.id, "image/png")
    new_path = storage.build_logo_path(organization.id, "image/jpeg")
    storage.objects[old_path] = StoredObjectInfo(
        path=old_path,
        content_type="image/png",
        size=100,
    )
    storage.objects[new_path] = StoredObjectInfo(
        path=new_path,
        content_type="image/jpeg",
        size=200,
    )
    existing = OrganizationProfile(
        id=uuid4(),
        organization_id=organization.id,
        logo_path=old_path,
        created_at=_now(),
        updated_at=_now(),
    )
    service, _, session, _ = _service(
        organization,
        profiles=[existing],
        storage=storage,
    )

    response = await service.confirm_logo_upload(
        organization_id=organization.id,
        payload=LogoConfirmRequest(path=new_path),
    )

    assert existing.logo_path == new_path
    assert session.committed is True
    assert storage.deleted_paths == [old_path]
    assert new_path in (response.logo_url or "")


@pytest.mark.asyncio
async def test_authorized_user_can_remove_logo():
    organization = _organization()
    storage = FakeStorage()
    path = storage.build_logo_path(organization.id, "image/png")
    storage.objects[path] = StoredObjectInfo(path=path, content_type="image/png", size=10)
    existing = OrganizationProfile(
        id=uuid4(),
        organization_id=organization.id,
        logo_path=path,
        created_at=_now(),
        updated_at=_now(),
    )
    service, _, session, _ = _service(
        organization,
        profiles=[existing],
        storage=storage,
    )

    response = await service.delete_logo(organization_id=organization.id)

    assert existing.logo_path is None
    assert session.committed is True
    assert storage.deleted_paths == [path]
    assert response.logo_url is None


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_remove_logo():
    organization = _organization()
    user = SimpleNamespace(id=uuid4(), email="member@example.com")
    app, service = _build_app(
        current_user=user,
        role=OrganizationRole.MEMBER,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/organizations/{organization.id}/logo")

    assert response.status_code == 403
    assert service.delete_calls == []


@pytest.mark.asyncio
async def test_cross_tenant_logo_deletion_impossible():
    organization = _organization()
    other_id = uuid4()
    user = SimpleNamespace(id=uuid4(), email="owner@example.com")
    app, service = _build_app(
        current_user=user,
        role=OrganizationRole.OWNER,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/organizations/{other_id}/logo")

    assert response.status_code == 403
    assert service.delete_calls == []


@pytest.mark.asyncio
async def test_profile_returns_temporary_logo_url_not_persisted_path():
    organization = _organization()
    storage = FakeStorage()
    path = storage.build_logo_path(organization.id, "image/png")
    storage.objects[path] = StoredObjectInfo(path=path, content_type="image/png", size=10)
    existing = OrganizationProfile(
        id=uuid4(),
        organization_id=organization.id,
        logo_path=path,
        created_at=_now(),
        updated_at=_now(),
    )
    service, _, _, _ = _service(organization, profiles=[existing], storage=storage)

    response = await service.get_profile(organization)

    assert response.logo_url.startswith("https://example.test/read/")
    assert existing.logo_path == path
    assert "logo_path" not in response.model_dump()


def test_path_validation_rejects_traversal():
    storage = FakeStorage()
    organization_id = uuid4()
    assert not storage.is_valid_logo_path_for_organization(
        organization_id,
        f"organizations/{organization_id}/logo/../secrets.txt",
    )
