"""Plan definition and organization plan/seat entitlement tests."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient

from app.core.authorization import OrganizationPermission, OrganizationRole
from app.core.plans import (
    Feature,
    Limit,
    PlanKey,
    entitlements_for_plan,
    parse_plan_key,
    plan_get_limit,
    plan_has_feature,
)
from app.modules.auth.dependencies import get_current_user
from app.modules.memberships.authorization import require_organization_permission
from app.modules.memberships.context import OrganizationContext
from app.modules.memberships.exceptions import OrganizationMemberLimitReachedError
from app.modules.memberships.service import MembershipService
from app.modules.organizations.models import Organization
from app.modules.organizations.service import OrganizationService
from app.modules.plans.dependencies import get_plan_service
from app.modules.plans.exceptions import UnknownOrganizationPlanError
from app.modules.plans.models import OrganizationPlan
from app.modules.plans.router import router as organization_plans_router
from app.modules.plans.schemas import OrganizationPlanResponse
from app.modules.plans.service import PlanService


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- Plan definitions ---


def test_free_plan_entitlements():
    entitlements = entitlements_for_plan(PlanKey.FREE)
    assert entitlements.features[Feature.ANALYTICS_BASIC] is True
    assert entitlements.features[Feature.ANALYTICS_ADVANCED] is False
    assert entitlements.features[Feature.SUPPORT_PRIORITY] is False
    assert entitlements.limits[Limit.ORGANIZATION_MEMBERS] == 3


def test_standard_plan_entitlements():
    entitlements = entitlements_for_plan(PlanKey.STANDARD)
    assert entitlements.features[Feature.SUPPORT_PRIORITY] is True
    assert entitlements.features[Feature.ANALYTICS_ADVANCED] is False
    assert entitlements.limits[Limit.ORGANIZATION_MEMBERS] == 10


def test_premium_plan_entitlements():
    entitlements = entitlements_for_plan(PlanKey.PREMIUM)
    assert entitlements.features[Feature.ANALYTICS_ADVANCED] is True
    assert entitlements.features[Feature.SUPPORT_PRIORITY] is True
    assert entitlements.limits[Limit.ORGANIZATION_MEMBERS] == 50


def test_enterprise_member_limit_is_unlimited():
    assert plan_get_limit(PlanKey.ENTERPRISE, Limit.ORGANIZATION_MEMBERS) is None
    assert plan_has_feature(PlanKey.ENTERPRISE, Feature.ANALYTICS_ADVANCED) is True


def test_unknown_plan_fails_safely():
    with pytest.raises(ValueError, match="Unknown organization plan"):
        parse_plan_key("platinum")


# --- Organization plan service ---


class FakePlanRepository:
    def __init__(self, plans: list[OrganizationPlan] | None = None) -> None:
        self.plans = plans or []
        self.create_calls = 0
        self.lock_calls = 0

    async def create(self, organization_plan: OrganizationPlan) -> OrganizationPlan:
        self.create_calls += 1
        if organization_plan.id is None:
            organization_plan.id = uuid4()
        organization_plan.created_at = _now()
        organization_plan.updated_at = _now()
        self.plans.append(organization_plan)
        return organization_plan

    async def get_by_organization_id(self, organization_id):
        for plan in self.plans:
            if plan.organization_id == organization_id:
                return plan
        return None

    async def get_by_organization_id_for_update(self, organization_id):
        self.lock_calls += 1
        return await self.get_by_organization_id(organization_id)


class FakeMembershipCountRepository:
    def __init__(self, *, members: int = 0) -> None:
        self.members = members
        self.memberships: dict = {}

    async def count_members(self, organization_id) -> int:
        return self.members

    async def get_by_organization_and_user(self, organization_id, user_id):
        return self.memberships.get((organization_id, user_id))

    async def create_owner_membership(self, *, organization_id, user_id):
        membership = SimpleNamespace(
            id=uuid4(),
            organization_id=organization_id,
            user_id=user_id,
            role=OrganizationRole.OWNER.value,
        )
        self.memberships[(organization_id, user_id)] = membership
        self.members += 1
        return membership


class FakeInvitationCountRepository:
    def __init__(self, *, pending: int = 0) -> None:
        self.pending = pending
        self.created: list = []
        self.pending_by_email: dict = {}

    async def count_pending(self, organization_id) -> int:
        return self.pending

    async def get_pending_by_organization_and_email(self, organization_id, email):
        return self.pending_by_email.get((organization_id, email))

    async def create(self, invitation):
        invitation.id = uuid4()
        invitation.created_at = _now()
        self.created.append(invitation)
        self.pending += 1
        return invitation


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


class FakeOrganizationRepository:
    def __init__(self) -> None:
        self.created: list[Organization] = []
        self.slugs: set[str] = set()

    async def create(self, organization: Organization) -> Organization:
        organization.id = uuid4()
        organization.created_at = _now()
        organization.updated_at = _now()
        self.created.append(organization)
        self.slugs.add(organization.slug)
        return organization

    async def get_by_slug(self, slug: str):
        return SimpleNamespace(id=uuid4()) if slug in self.slugs else None


@pytest.mark.asyncio
async def test_new_organization_atomically_receives_free_plan():
    session = FakeSession()
    org_repo = FakeOrganizationRepository()
    membership_repo = FakeMembershipCountRepository()
    plan_repo = FakePlanRepository()
    service = OrganizationService(
        session=session,
        organization_repository=org_repo,
        membership_repository=membership_repo,
        profile_repository=SimpleNamespace(),
        plan_repository=plan_repo,
        storage=SimpleNamespace(),
    )
    user = SimpleNamespace(id=uuid4())

    response = await service.create_organization(user, "Acme Co")

    assert session.committed is True
    assert len(org_repo.created) == 1
    assert membership_repo.members == 1
    assert plan_repo.create_calls == 1
    assert plan_repo.plans[0].plan_key == PlanKey.FREE.value
    assert plan_repo.plans[0].organization_id == response.id


@pytest.mark.asyncio
async def test_get_entitlements_and_seat_usage():
    organization_id = uuid4()
    plan_repo = FakePlanRepository(
        [
            OrganizationPlan(
                id=uuid4(),
                organization_id=organization_id,
                plan_key=PlanKey.FREE.value,
                created_at=_now(),
                updated_at=_now(),
            )
        ]
    )
    service = PlanService(
        session=FakeSession(),
        plan_repository=plan_repo,
        membership_repository=FakeMembershipCountRepository(members=1),
        invitation_repository=FakeInvitationCountRepository(pending=1),
    )

    response = await service.get_organization_plan_response(organization_id)

    assert response.plan == "free"
    assert response.features["analytics.basic"] is True
    assert response.features["analytics.advanced"] is False
    assert response.limits["organization.members"] == 3
    assert response.usage["organization.members"] == 2


@pytest.mark.asyncio
async def test_unknown_persisted_plan_does_not_grant_paid_entitlements():
    organization_id = uuid4()
    plan_repo = FakePlanRepository(
        [
            OrganizationPlan(
                id=uuid4(),
                organization_id=organization_id,
                plan_key="platinum",
                created_at=_now(),
                updated_at=_now(),
            )
        ]
    )
    service = PlanService(
        session=FakeSession(),
        plan_repository=plan_repo,
        membership_repository=FakeMembershipCountRepository(),
        invitation_repository=FakeInvitationCountRepository(),
    )

    with pytest.raises(UnknownOrganizationPlanError):
        await service.get_organization_plan_key(organization_id)


@pytest.mark.asyncio
async def test_seat_limit_blocks_invitation_at_capacity():
    organization_id = uuid4()
    plan_repo = FakePlanRepository(
        [
            OrganizationPlan(
                id=uuid4(),
                organization_id=organization_id,
                plan_key=PlanKey.FREE.value,
                created_at=_now(),
                updated_at=_now(),
            )
        ]
    )
    membership_repo = FakeMembershipCountRepository(members=2)
    invitation_repo = FakeInvitationCountRepository(pending=1)
    service = MembershipService(
        session=FakeSession(),
        membership_repository=membership_repo,
        invitation_repository=invitation_repo,
        user_repository=SimpleNamespace(get_by_email=lambda _email: None),
        plan_repository=plan_repo,
        settings=SimpleNamespace(invitation_expiry_days=7, app_env="test"),
    )

    with pytest.raises(OrganizationMemberLimitReachedError):
        await service.create_invitation(
            organization_id,
            SimpleNamespace(id=uuid4()),
            "person@example.com",
        )

    assert invitation_repo.created == []
    assert plan_repo.lock_calls == 1


@pytest.mark.asyncio
async def test_invitation_allowed_below_limit():
    organization_id = uuid4()
    plan_repo = FakePlanRepository(
        [
            OrganizationPlan(
                id=uuid4(),
                organization_id=organization_id,
                plan_key=PlanKey.FREE.value,
                created_at=_now(),
                updated_at=_now(),
            )
        ]
    )
    membership_repo = FakeMembershipCountRepository(members=1)
    invitation_repo = FakeInvitationCountRepository(pending=0)

    async def get_by_email(_email):
        return None

    service = MembershipService(
        session=FakeSession(),
        membership_repository=membership_repo,
        invitation_repository=invitation_repo,
        user_repository=SimpleNamespace(get_by_email=get_by_email),
        plan_repository=plan_repo,
        settings=SimpleNamespace(
            invitation_expiry_days=7,
            app_env="test",
            frontend_app_url="http://localhost:3000",
        ),
    )

    invitation, _ = await service.create_invitation(
        organization_id,
        SimpleNamespace(id=uuid4()),
        "person@example.com",
    )

    assert invitation.email == "person@example.com"
    assert len(invitation_repo.created) == 1


@pytest.mark.asyncio
async def test_enterprise_unlimited_allows_invite_regardless_of_usage():
    organization_id = uuid4()
    plan_repo = FakePlanRepository(
        [
            OrganizationPlan(
                id=uuid4(),
                organization_id=organization_id,
                plan_key=PlanKey.ENTERPRISE.value,
                created_at=_now(),
                updated_at=_now(),
            )
        ]
    )
    membership_repo = FakeMembershipCountRepository(members=100)
    invitation_repo = FakeInvitationCountRepository(pending=50)

    async def get_by_email(_email):
        return None

    service = MembershipService(
        session=FakeSession(),
        membership_repository=membership_repo,
        invitation_repository=invitation_repo,
        user_repository=SimpleNamespace(get_by_email=get_by_email),
        plan_repository=plan_repo,
        settings=SimpleNamespace(
            invitation_expiry_days=7,
            app_env="test",
            frontend_app_url="http://localhost:3000",
        ),
    )

    invitation, _ = await service.create_invitation(
        organization_id,
        SimpleNamespace(id=uuid4()),
        "enterprise@example.com",
    )

    assert invitation is not None
    assert len(invitation_repo.created) == 1


@pytest.mark.asyncio
async def test_revoked_and_expired_invitations_are_excluded_from_pending_count_logic():
    """count_pending is repository-owned; verify PlanService uses its return value."""
    organization_id = uuid4()
    plan_repo = FakePlanRepository(
        [
            OrganizationPlan(
                id=uuid4(),
                organization_id=organization_id,
                plan_key=PlanKey.FREE.value,
                created_at=_now(),
                updated_at=_now(),
            )
        ]
    )
    # Simulate repository already excluding revoked/expired (pending=0).
    service = PlanService(
        session=FakeSession(),
        plan_repository=plan_repo,
        membership_repository=FakeMembershipCountRepository(members=2),
        invitation_repository=FakeInvitationCountRepository(pending=0),
    )

    assert await service.count_member_seats(organization_id) == 2


def test_organization_plan_response_uses_null_for_unlimited():
    response = OrganizationPlanResponse(
        plan="enterprise",
        features={"analytics.basic": True},
        limits={"organization.members": None},
        usage={"organization.members": 12},
    )
    assert response.model_dump()["limits"]["organization.members"] is None


# --- Plan API auth ---


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


@pytest.mark.asyncio
async def test_member_can_read_plan_api():
    organization = Organization(
        id=uuid4(),
        name="Acme",
        slug="acme",
        created_at=_now(),
        updated_at=_now(),
    )
    user = SimpleNamespace(id=uuid4(), email="member@example.com")
    app = FastAPI()
    app.include_router(organization_plans_router, prefix="/organizations")

    class FakePlanService:
        async def get_organization_plan_response(self, organization_id):
            return OrganizationPlanResponse(
                plan="free",
                features={
                    "analytics.basic": True,
                    "analytics.advanced": False,
                    "support.priority": False,
                },
                limits={"organization.members": 3},
                usage={"organization.members": 1},
            )

    async def override_current_user():
        return user

    async def override_plan_service():
        return FakePlanService()

    async def allow_view(organization_id):
        if str(organization_id) != str(organization.id):
            raise HTTPException(status_code=403, detail="Forbidden")
        return _make_context(user=user, organization=organization, role=OrganizationRole.MEMBER)

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_plan_service] = override_plan_service
    app.dependency_overrides[
        require_organization_permission(OrganizationPermission.ORGANIZATION_VIEW)
    ] = allow_view

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/organizations/{organization.id}/plan")

    assert response.status_code == 200
    assert response.json()["plan"] == "free"
    assert response.json()["limits"]["organization.members"] == 3


@pytest.mark.asyncio
async def test_outsider_cannot_read_plan_api():
    organization = Organization(
        id=uuid4(),
        name="Acme",
        slug="acme",
        created_at=_now(),
        updated_at=_now(),
    )
    user = SimpleNamespace(id=uuid4(), email="outsider@example.com")
    app = FastAPI()
    app.include_router(organization_plans_router, prefix="/organizations")

    async def override_current_user():
        return user

    async def deny_view(organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[
        require_organization_permission(OrganizationPermission.ORGANIZATION_VIEW)
    ] = deny_view

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/organizations/{organization.id}/plan")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_concurrent_style_second_invite_hits_limit_after_first():
    """Simulate serialized invites: after first succeeds, second is blocked."""
    organization_id = uuid4()
    plan_repo = FakePlanRepository(
        [
            OrganizationPlan(
                id=uuid4(),
                organization_id=organization_id,
                plan_key=PlanKey.FREE.value,
                created_at=_now(),
                updated_at=_now(),
            )
        ]
    )
    membership_repo = FakeMembershipCountRepository(members=2)
    invitation_repo = FakeInvitationCountRepository(pending=0)

    async def get_by_email(_email):
        return None

    service = MembershipService(
        session=FakeSession(),
        membership_repository=membership_repo,
        invitation_repository=invitation_repo,
        user_repository=SimpleNamespace(get_by_email=get_by_email),
        plan_repository=plan_repo,
        settings=SimpleNamespace(
            invitation_expiry_days=7,
            app_env="test",
            frontend_app_url="http://localhost:3000",
        ),
    )

    await service.create_invitation(
        organization_id,
        SimpleNamespace(id=uuid4()),
        "first@example.com",
    )
    # usage becomes 3 (2 members + 1 pending)
    with pytest.raises(OrganizationMemberLimitReachedError):
        await service.create_invitation(
            organization_id,
            SimpleNamespace(id=uuid4()),
            "second@example.com",
        )

    assert len(invitation_repo.created) == 1
    assert plan_repo.lock_calls == 2
