"""Subscription foundation service and API tests."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient

from app.core.authorization import OrganizationPermission, OrganizationRole
from app.core.plans import PlanKey
from app.core.subscriptions import (
    BillingInterval,
    SubscriptionProvider,
    SubscriptionStatus,
)
from app.modules.auth.dependencies import get_current_user
from app.modules.memberships.authorization import require_organization_permission
from app.modules.memberships.context import OrganizationContext
from app.modules.organizations.models import Organization
from app.modules.plans.models import OrganizationPlan
from app.modules.subscriptions.dependencies import get_subscription_service
from app.modules.subscriptions.models import OrganizationSubscription
from app.modules.subscriptions.router import router as organization_subscriptions_router
from app.modules.subscriptions.schemas import OrganizationSubscriptionResponse
from app.modules.subscriptions.service import SubscriptionService


def _now() -> datetime:
    return datetime.now(timezone.utc)


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


class FakeSubscriptionRepository:
    def __init__(self, subscriptions: list[OrganizationSubscription] | None = None) -> None:
        self.subscriptions = subscriptions or []
        self.create_calls = 0

    async def create(self, subscription: OrganizationSubscription) -> OrganizationSubscription:
        self.create_calls += 1
        if subscription.id is None:
            subscription.id = uuid4()
        subscription.created_at = _now()
        subscription.updated_at = _now()
        self.subscriptions.append(subscription)
        return subscription

    async def get_by_organization_id(self, organization_id):
        for item in self.subscriptions:
            if item.organization_id == organization_id:
                return item
        return None

    async def get_by_organization_id_for_update(self, organization_id):
        return await self.get_by_organization_id(organization_id)


class FakePlanRepository:
    def __init__(self, plans: list[OrganizationPlan] | None = None) -> None:
        self.plans = plans or []
        self.create_calls = 0

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


def _service(
    *,
    subscriptions: list[OrganizationSubscription] | None = None,
    plans: list[OrganizationPlan] | None = None,
) -> tuple[SubscriptionService, FakeSubscriptionRepository, FakePlanRepository, FakeSession]:
    session = FakeSession()
    subscription_repo = FakeSubscriptionRepository(subscriptions)
    plan_repo = FakePlanRepository(plans)
    service = SubscriptionService(
        session=session,
        subscription_repository=subscription_repo,
        plan_repository=plan_repo,
    )
    return service, subscription_repo, plan_repo, session


@pytest.mark.asyncio
async def test_create_initial_subscription_is_free_active_none():
    organization_id = uuid4()
    service, subscription_repo, plan_repo, _ = _service()

    subscription = await service.create_initial_subscription(organization_id)

    assert subscription_repo.create_calls == 1
    assert subscription.provider == SubscriptionProvider.NONE.value
    assert subscription.status == SubscriptionStatus.ACTIVE.value
    assert subscription.plan_key == PlanKey.FREE.value
    assert subscription.billing_interval == BillingInterval.MONTHLY.value
    assert plan_repo.create_calls == 1
    assert plan_repo.plans[0].plan_key == PlanKey.FREE.value


@pytest.mark.asyncio
async def test_change_plan_synchronizes_organization_plan():
    organization_id = uuid4()
    now = _now()
    subscription = OrganizationSubscription(
        id=uuid4(),
        organization_id=organization_id,
        provider=SubscriptionProvider.NONE.value,
        plan_key=PlanKey.FREE.value,
        status=SubscriptionStatus.ACTIVE.value,
        billing_interval=BillingInterval.MONTHLY.value,
        current_period_start=now,
        current_period_end=now,
        cancel_at_period_end=False,
        created_at=now,
        updated_at=now,
    )
    plan = OrganizationPlan(
        id=uuid4(),
        organization_id=organization_id,
        plan_key=PlanKey.FREE.value,
        created_at=now,
        updated_at=now,
    )
    service, _, plan_repo, session = _service(
        subscriptions=[subscription],
        plans=[plan],
    )

    updated = await service.change_plan(organization_id, PlanKey.PREMIUM)

    assert updated.plan_key == PlanKey.PREMIUM.value
    assert plan_repo.plans[0].plan_key == PlanKey.PREMIUM.value
    assert session.committed is True


@pytest.mark.asyncio
async def test_expire_subscription_falls_back_to_free_plan():
    organization_id = uuid4()
    now = _now()
    subscription = OrganizationSubscription(
        id=uuid4(),
        organization_id=organization_id,
        provider=SubscriptionProvider.STRIPE.value,
        plan_key=PlanKey.STANDARD.value,
        status=SubscriptionStatus.ACTIVE.value,
        billing_interval=BillingInterval.MONTHLY.value,
        current_period_start=now,
        current_period_end=now,
        cancel_at_period_end=True,
        created_at=now,
        updated_at=now,
    )
    plan = OrganizationPlan(
        id=uuid4(),
        organization_id=organization_id,
        plan_key=PlanKey.STANDARD.value,
        created_at=now,
        updated_at=now,
    )
    service, _, plan_repo, _ = _service(
        subscriptions=[subscription],
        plans=[plan],
    )

    expired = await service.expire_subscription(organization_id)

    assert expired.status == SubscriptionStatus.EXPIRED.value
    assert expired.plan_key == PlanKey.FREE.value
    assert plan_repo.plans[0].plan_key == PlanKey.FREE.value


@pytest.mark.asyncio
async def test_activate_subscription_clears_cancellation_flags():
    organization_id = uuid4()
    now = _now()
    subscription = OrganizationSubscription(
        id=uuid4(),
        organization_id=organization_id,
        provider=SubscriptionProvider.NONE.value,
        plan_key=PlanKey.FREE.value,
        status=SubscriptionStatus.CANCELED.value,
        billing_interval=BillingInterval.MONTHLY.value,
        current_period_start=now,
        current_period_end=now,
        cancel_at_period_end=True,
        canceled_at=now,
        created_at=now,
        updated_at=now,
    )
    plan = OrganizationPlan(
        id=uuid4(),
        organization_id=organization_id,
        plan_key=PlanKey.FREE.value,
        created_at=now,
        updated_at=now,
    )
    service, _, _, _ = _service(subscriptions=[subscription], plans=[plan])

    activated = await service.activate_subscription(
        organization_id,
        plan_key=PlanKey.STANDARD,
    )

    assert activated.status == SubscriptionStatus.ACTIVE.value
    assert activated.plan_key == PlanKey.STANDARD.value
    assert activated.cancel_at_period_end is False
    assert activated.canceled_at is None


@pytest.mark.asyncio
async def test_subscription_response_hides_provider_ids():
    organization_id = uuid4()
    now = _now()
    subscription = OrganizationSubscription(
        id=uuid4(),
        organization_id=organization_id,
        provider=SubscriptionProvider.STRIPE.value,
        provider_customer_id="cus_secret",
        provider_subscription_id="sub_secret",
        plan_key=PlanKey.PREMIUM.value,
        status=SubscriptionStatus.ACTIVE.value,
        billing_interval=BillingInterval.YEARLY.value,
        current_period_start=now,
        current_period_end=now,
        cancel_at_period_end=False,
        created_at=now,
        updated_at=now,
    )
    service, _, _, _ = _service(subscriptions=[subscription])

    response = await service.get_subscription_response(organization_id)
    payload = response.model_dump()

    assert payload["plan"] == "premium"
    assert payload["provider"] == "stripe"
    assert "provider_customer_id" not in payload
    assert "provider_subscription_id" not in payload


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
async def test_member_can_read_subscription_api():
    organization = Organization(
        id=uuid4(),
        name="Acme",
        slug="acme",
        created_at=_now(),
        updated_at=_now(),
    )
    user = SimpleNamespace(id=uuid4(), email="member@example.com")
    app = FastAPI()
    app.include_router(organization_subscriptions_router, prefix="/organizations")
    now = _now()

    class FakeSubscriptionService:
        async def get_subscription_response(self, organization_id):
            return OrganizationSubscriptionResponse(
                plan="free",
                status="active",
                provider="none",
                billing_interval="monthly",
                current_period_start=now,
                current_period_end=now,
                cancel_at_period_end=False,
            )

    async def override_current_user():
        return user

    async def allow_view(organization_id):
        if str(organization_id) != str(organization.id):
            raise HTTPException(status_code=403, detail="Forbidden")
        return _make_context(
            user=user,
            organization=organization,
            role=OrganizationRole.MEMBER,
        )

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_subscription_service] = lambda: FakeSubscriptionService()
    app.dependency_overrides[
        require_organization_permission(OrganizationPermission.ORGANIZATION_VIEW)
    ] = allow_view

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/organizations/{organization.id}/subscription")

    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "free"
    assert body["status"] == "active"
    assert "provider_customer_id" not in body


@pytest.mark.asyncio
async def test_outsider_cannot_read_subscription_api():
    organization = Organization(
        id=uuid4(),
        name="Acme",
        slug="acme",
        created_at=_now(),
        updated_at=_now(),
    )
    user = SimpleNamespace(id=uuid4(), email="outsider@example.com")
    app = FastAPI()
    app.include_router(organization_subscriptions_router, prefix="/organizations")

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
        response = await client.get(f"/organizations/{organization.id}/subscription")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cross_tenant_subscription_access_denied():
    organization = Organization(
        id=uuid4(),
        name="Acme",
        slug="acme",
        created_at=_now(),
        updated_at=_now(),
    )
    other_id = uuid4()
    user = SimpleNamespace(id=uuid4(), email="owner@example.com")
    app = FastAPI()
    app.include_router(organization_subscriptions_router, prefix="/organizations")

    async def override_current_user():
        return user

    async def allow_only_own(organization_id):
        if str(organization_id) != str(organization.id):
            raise HTTPException(status_code=403, detail="Forbidden")
        return _make_context(
            user=user,
            organization=organization,
            role=OrganizationRole.OWNER,
        )

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[
        require_organization_permission(OrganizationPermission.ORGANIZATION_VIEW)
    ] = allow_only_own

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/organizations/{other_id}/subscription")

    assert response.status_code == 403
