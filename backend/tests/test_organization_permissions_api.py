"""API authorization behavior tests with dependency overrides."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient

from app.core.authorization import OrganizationPermission, OrganizationRole
from app.modules.auth.dependencies import get_current_user
from app.modules.memberships.authorization import require_organization_permission
from app.modules.memberships.context import OrganizationContext
from app.modules.memberships.dependencies import get_membership_service
from app.modules.memberships.router import organization_memberships_router


def _make_context(*, user, organization_id, role: OrganizationRole) -> OrganizationContext:
    now = datetime.now(timezone.utc)
    organization = SimpleNamespace(
        id=organization_id,
        name="Acme",
        slug="acme",
        created_at=now,
        updated_at=now,
    )
    membership = SimpleNamespace(
        id=uuid4(),
        organization_id=organization_id,
        user_id=user.id,
        role=role.value,
        created_at=now,
    )
    return OrganizationContext.from_membership(
        user=user,
        organization=organization,
        membership=membership,
    )


class FakeMembershipService:
    def __init__(self) -> None:
        self.created_invitations: list[tuple] = []
        self.revoked_invitations: list[tuple] = []

    async def list_members(self, organization_id):
        return []

    async def list_pending_invitations(self, organization_id):
        return []

    async def create_invitation(self, organization_id, user, email):
        self.created_invitations.append((organization_id, user.id, email))
        now = datetime.now(timezone.utc)
        invitation = SimpleNamespace(
            id=uuid4(),
            organization_id=organization_id,
            email=email,
            role=OrganizationRole.MEMBER.value,
            expires_at=now,
            created_at=now,
        )
        return invitation, None

    async def revoke_invitation(self, organization_id, invitation_id):
        self.revoked_invitations.append((organization_id, invitation_id))
        now = datetime.now(timezone.utc)
        return SimpleNamespace(
            id=invitation_id,
            organization_id=organization_id,
            email="person@example.com",
            role=OrganizationRole.MEMBER.value,
            expires_at=now,
            created_at=now,
            revoked_at=now,
        )


def _build_app(*, current_user, role: OrganizationRole | None):
    app = FastAPI()
    app.include_router(organization_memberships_router, prefix="/organizations")
    service = FakeMembershipService()

    async def override_current_user():
        return current_user

    async def override_membership_service():
        return service

    permission_allowed = {
        OrganizationPermission.MEMBER_VIEW: role
        in {OrganizationRole.OWNER, OrganizationRole.MEMBER},
        OrganizationPermission.INVITATION_VIEW: role == OrganizationRole.OWNER,
        OrganizationPermission.MEMBER_INVITE: role == OrganizationRole.OWNER,
        OrganizationPermission.INVITATION_REVOKE: role == OrganizationRole.OWNER,
    }

    for permission, allowed in permission_allowed.items():
        def make_override(is_allowed: bool = allowed, current_role: OrganizationRole | None = role):
            async def dependency(organization_id):
                if current_role is None or not is_allowed:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Forbidden",
                    )
                return _make_context(
                    user=current_user,
                    organization_id=organization_id,
                    role=current_role,
                )

            return dependency

        app.dependency_overrides[require_organization_permission(permission)] = (
            make_override()
        )

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_membership_service] = override_membership_service
    return app, service


@pytest.mark.asyncio
async def test_unauthenticated_members_list_returns_401():
    organization_id = uuid4()
    app = FastAPI()
    app.include_router(organization_memberships_router, prefix="/organizations")

    async def deny_auth():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    app.dependency_overrides[get_current_user] = deny_auth

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/organizations/{organization_id}/members")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_member_can_list_members_but_cannot_invite():
    organization_id = uuid4()
    member_user = SimpleNamespace(id=uuid4(), email="member@example.com")
    app, service = _build_app(current_user=member_user, role=OrganizationRole.MEMBER)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_response = await client.get(f"/organizations/{organization_id}/members")
        invite_response = await client.post(
            f"/organizations/{organization_id}/invitations",
            json={"email": "new@example.com"},
        )

    assert list_response.status_code == 200
    assert invite_response.status_code == 403
    assert service.created_invitations == []


@pytest.mark.asyncio
async def test_owner_can_create_and_revoke_invitation():
    organization_id = uuid4()
    owner_user = SimpleNamespace(id=uuid4(), email="owner@example.com")
    invitation_id = uuid4()
    app, service = _build_app(current_user=owner_user, role=OrganizationRole.OWNER)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            f"/organizations/{organization_id}/invitations",
            json={"email": "new@example.com"},
        )
        revoke_response = await client.delete(
            f"/organizations/{organization_id}/invitations/{invitation_id}",
        )

    assert create_response.status_code == 201
    assert revoke_response.status_code == 204
    assert len(service.created_invitations) == 1
    assert service.revoked_invitations[0][0] == organization_id or str(
        service.revoked_invitations[0][0]
    ) == str(organization_id)
    assert service.revoked_invitations[0][1] == invitation_id


@pytest.mark.asyncio
async def test_outsider_cannot_list_members():
    organization_id = uuid4()
    outsider_user = SimpleNamespace(id=uuid4(), email="outsider@example.com")
    app, _service = _build_app(current_user=outsider_user, role=None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/organizations/{organization_id}/members")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_member_cannot_revoke_invitation():
    organization_id = uuid4()
    member_user = SimpleNamespace(id=uuid4(), email="member@example.com")
    invitation_id = uuid4()
    app, service = _build_app(current_user=member_user, role=OrganizationRole.MEMBER)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/organizations/{organization_id}/invitations/{invitation_id}",
        )

    assert response.status_code == 403
    assert service.revoked_invitations == []
