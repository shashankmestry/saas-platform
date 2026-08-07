"""Organization profile service, schema, and API authorization tests."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.authorization import OrganizationPermission, OrganizationRole
from app.modules.auth.dependencies import get_current_user
from app.modules.memberships.authorization import require_organization_permission
from app.modules.memberships.context import OrganizationContext
from app.modules.organizations.dependencies import get_organization_service
from app.modules.organizations.models import Organization, OrganizationProfile
from app.modules.organizations.router import router as organizations_router
from app.modules.organizations.schemas import (
    OrganizationProfileUpdate,
)
from app.modules.organizations.service import OrganizationService


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _organization(*, organization_id=None, name="Acme", slug="acme") -> Organization:
    return Organization(
        id=organization_id or uuid4(),
        name=name,
        slug=slug,
        created_at=_now(),
        updated_at=_now(),
    )


class FakeOrganizationRepository:
    def __init__(self, organizations: list[Organization] | None = None) -> None:
        self.organizations = organizations or []

    async def get_by_id(self, organization_id):
        for organization in self.organizations:
            if organization.id == organization_id:
                return organization
        return None


class FakeProfileRepository:
    def __init__(self, profiles: list[OrganizationProfile] | None = None) -> None:
        self.profiles = profiles or []
        self.create_calls = 0
        self.fail_on_create = False

    async def get_by_organization_id(self, organization_id):
        for profile in self.profiles:
            if profile.organization_id == organization_id:
                return profile
        return None

    async def create(self, profile: OrganizationProfile) -> OrganizationProfile:
        self.create_calls += 1
        if self.fail_on_create:
            raise RuntimeError("profile create failed")
        if any(item.organization_id == profile.organization_id for item in self.profiles):
            raise RuntimeError("organization_id must be unique")
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
        self.flush_count = 0

    async def flush(self) -> None:
        self.flush_count += 1

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def refresh(self, _obj) -> None:
        return None


def _service(
    organization: Organization,
    profiles: list[OrganizationProfile] | None = None,
) -> tuple[OrganizationService, FakeProfileRepository, FakeSession]:
    session = FakeSession()
    profile_repository = FakeProfileRepository(profiles)

    async def create_signed_read_url(_path: str):
        return None

    storage = SimpleNamespace(create_signed_read_url=create_signed_read_url)
    service = OrganizationService(
        session=session,
        organization_repository=FakeOrganizationRepository([organization]),
        membership_repository=SimpleNamespace(),
        profile_repository=profile_repository,
        plan_repository=SimpleNamespace(),
        subscription_service=SimpleNamespace(),
        storage=storage,
    )
    return service, profile_repository, session


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
        self.profile = None
        self.update_calls: list = []

    async def get_profile(self, organization: Organization):
        profile = self.profile
        return {
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug,
            "website": profile.website if profile else None,
            "contact_email": profile.contact_email if profile else None,
            "phone": profile.phone if profile else None,
            "country_code": profile.country_code if profile else None,
            "timezone": profile.timezone if profile else None,
            "default_currency": profile.default_currency if profile else None,
            "logo_url": None,
        }

    async def update_profile(self, *, organization_id, payload: OrganizationProfileUpdate):
        self.update_calls.append((organization_id, payload))
        if payload.name is not None:
            self.organization.name = payload.name
        if self.profile is None:
            self.profile = SimpleNamespace(
                website=payload.website,
                contact_email=(
                    str(payload.contact_email) if payload.contact_email is not None else None
                ),
                phone=payload.phone,
                country_code=payload.country_code,
                timezone=payload.timezone,
                default_currency=payload.default_currency,
            )
        else:
            data = payload.model_dump(exclude_unset=True)
            data.pop("name", None)
            for key, value in data.items():
                setattr(self.profile, key, value)
        return await self.get_profile(self.organization)


def _build_profile_app(*, current_user, role: OrganizationRole | None, organization):
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


# --- Schema validation ---


def test_country_code_normalization():
    payload = OrganizationProfileUpdate(country_code=" in ")
    assert payload.country_code == "IN"


def test_currency_normalization():
    payload = OrganizationProfileUpdate(default_currency="usd")
    assert payload.default_currency == "USD"


def test_invalid_email_rejected():
    with pytest.raises(ValidationError):
        OrganizationProfileUpdate(contact_email="not-an-email")


def test_invalid_profile_data_rejected():
    with pytest.raises(ValidationError):
        OrganizationProfileUpdate(website="example.com")
    with pytest.raises(ValidationError):
        OrganizationProfileUpdate(country_code="IND")
    with pytest.raises(ValidationError):
        OrganizationProfileUpdate(default_currency="US")
    with pytest.raises(ValidationError):
        OrganizationProfileUpdate(timezone="Not/AZone")
    with pytest.raises(ValidationError):
        OrganizationProfileUpdate(name=" ")


def test_empty_optional_fields_become_none():
    payload = OrganizationProfileUpdate(
        website="",
        phone="",
        country_code="",
        timezone="",
        default_currency="",
    )
    assert payload.website is None
    assert payload.phone is None
    assert payload.country_code is None
    assert payload.timezone is None
    assert payload.default_currency is None


def test_organization_id_unique_on_model():
    column = OrganizationProfile.__table__.c.organization_id
    assert column.unique is True


# --- Service behavior ---


@pytest.mark.asyncio
async def test_get_profile_returns_nulls_without_creating_row():
    organization = _organization()
    service, profile_repository, session = _service(organization)

    response = await service.get_profile(organization)

    assert response.name == organization.name
    assert response.slug == organization.slug
    assert response.website is None
    assert profile_repository.create_calls == 0
    assert session.committed is False


@pytest.mark.asyncio
async def test_first_patch_creates_profile():
    organization = _organization()
    service, profile_repository, session = _service(organization)

    response = await service.update_profile(
        organization_id=organization.id,
        payload=OrganizationProfileUpdate(
            website="https://acme.example",
            country_code="in",
            default_currency="inr",
        ),
    )

    assert profile_repository.create_calls == 1
    assert len(profile_repository.profiles) == 1
    assert session.committed is True
    assert response.website == "https://acme.example"
    assert response.country_code == "IN"
    assert response.default_currency == "INR"


@pytest.mark.asyncio
async def test_later_patch_updates_existing_profile():
    organization = _organization()
    existing = OrganizationProfile(
        id=uuid4(),
        organization_id=organization.id,
        website="https://old.example",
        created_at=_now(),
        updated_at=_now(),
    )
    service, profile_repository, session = _service(organization, [existing])

    response = await service.update_profile(
        organization_id=organization.id,
        payload=OrganizationProfileUpdate(website="https://new.example"),
    )

    assert profile_repository.create_calls == 0
    assert len(profile_repository.profiles) == 1
    assert response.website == "https://new.example"
    assert session.committed is True


@pytest.mark.asyncio
async def test_authorized_user_can_update_organization_name():
    organization = _organization(name="Old Name")
    service, _, session = _service(organization)

    response = await service.update_profile(
        organization_id=organization.id,
        payload=OrganizationProfileUpdate(name="New Name"),
    )

    assert organization.name == "New Name"
    assert response.name == "New Name"
    assert response.slug == "acme"
    assert session.committed is True


@pytest.mark.asyncio
async def test_slug_cannot_be_changed_through_profile_update():
    organization = _organization(slug="original-slug")
    service, _, _ = _service(organization)

    # Extra slug field is ignored by the update schema.
    payload = OrganizationProfileUpdate.model_validate(
        {"name": "Still Acme", "slug": "hijacked-slug"},
    )
    response = await service.update_profile(
        organization_id=organization.id,
        payload=payload,
    )

    assert organization.slug == "original-slug"
    assert response.slug == "original-slug"
    assert "slug" not in OrganizationProfileUpdate.model_fields


@pytest.mark.asyncio
async def test_name_and_profile_update_is_atomic_on_failure():
    organization = _organization(name="Original")
    service, profile_repository, session = _service(organization)
    profile_repository.fail_on_create = True

    with pytest.raises(RuntimeError, match="profile create failed"):
        await service.update_profile(
            organization_id=organization.id,
            payload=OrganizationProfileUpdate(
                name="Changed",
                website="https://acme.example",
            ),
        )

    assert session.rolled_back is True
    assert session.committed is False
    assert profile_repository.create_calls == 1
    assert len(profile_repository.profiles) == 0


@pytest.mark.asyncio
async def test_duplicate_profile_create_is_rejected():
    organization = _organization()
    existing = OrganizationProfile(
        id=uuid4(),
        organization_id=organization.id,
        created_at=_now(),
        updated_at=_now(),
    )
    repository = FakeProfileRepository([existing])

    with pytest.raises(RuntimeError, match="organization_id must be unique"):
        await repository.create(
            OrganizationProfile(organization_id=organization.id),
        )


# --- API authorization ---


@pytest.mark.asyncio
async def test_member_with_view_can_read_profile():
    organization = _organization()
    user = SimpleNamespace(id=uuid4(), email="member@example.com")
    app, _ = _build_profile_app(
        current_user=user,
        role=OrganizationRole.MEMBER,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/organizations/{organization.id}/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(organization.id)
    assert body["name"] == organization.name
    assert body["website"] is None


@pytest.mark.asyncio
async def test_user_outside_organization_cannot_read_profile():
    organization = _organization()
    user = SimpleNamespace(id=uuid4(), email="outsider@example.com")
    app, _ = _build_profile_app(
        current_user=user,
        role=None,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/organizations/{organization.id}/profile")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_member_without_manage_cannot_update_profile():
    organization = _organization()
    user = SimpleNamespace(id=uuid4(), email="member@example.com")
    app, service = _build_profile_app(
        current_user=user,
        role=OrganizationRole.MEMBER,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/organizations/{organization.id}/profile",
            json={"name": "Nope"},
        )

    assert response.status_code == 403
    assert service.update_calls == []


@pytest.mark.asyncio
async def test_owner_can_update_profile_via_api():
    organization = _organization()
    user = SimpleNamespace(id=uuid4(), email="owner@example.com")
    app, service = _build_profile_app(
        current_user=user,
        role=OrganizationRole.OWNER,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/organizations/{organization.id}/profile",
            json={
                "name": "Acme Updated",
                "website": "https://acme.example",
                "country_code": "us",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Acme Updated"
    assert body["website"] == "https://acme.example"
    assert body["country_code"] == "US"
    assert len(service.update_calls) == 1


@pytest.mark.asyncio
async def test_cross_tenant_update_is_impossible():
    organization = _organization()
    other_organization_id = uuid4()
    user = SimpleNamespace(id=uuid4(), email="owner@example.com")
    app, service = _build_profile_app(
        current_user=user,
        role=OrganizationRole.OWNER,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/organizations/{other_organization_id}/profile",
            json={"name": "Hijack"},
        )

    assert response.status_code == 403
    assert service.update_calls == []


@pytest.mark.asyncio
async def test_invalid_email_returns_validation_error_from_api():
    organization = _organization()
    user = SimpleNamespace(id=uuid4(), email="owner@example.com")
    app, _ = _build_profile_app(
        current_user=user,
        role=OrganizationRole.OWNER,
        organization=organization,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/organizations/{organization.id}/profile",
            json={"contact_email": "bad-email"},
        )

    assert response.status_code == 422
