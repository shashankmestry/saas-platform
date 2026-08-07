from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import PlanKey, parse_plan_key
from app.core.subscriptions import (
    BillingInterval,
    SubscriptionProvider,
    SubscriptionStatus,
)
from app.modules.plans.models import OrganizationPlan
from app.modules.plans.repository import OrganizationPlanRepository
from app.modules.subscriptions.exceptions import (
    InvalidSubscriptionStateError,
    OrganizationSubscriptionNotFoundError,
)
from app.modules.subscriptions.models import OrganizationSubscription
from app.modules.subscriptions.repository import OrganizationSubscriptionRepository
from app.modules.subscriptions.schemas import OrganizationSubscriptionResponse


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def period_end_for_interval(
    start: datetime,
    billing_interval: BillingInterval,
) -> datetime:
    """Approximate period end using calendar-independent day offsets."""
    if billing_interval == BillingInterval.YEARLY:
        return start + timedelta(days=365)
    return start + timedelta(days=30)


class SubscriptionService:
    """Manages commercial subscription state and OrganizationPlan synchronization."""

    def __init__(
        self,
        session: AsyncSession,
        subscription_repository: OrganizationSubscriptionRepository,
        plan_repository: OrganizationPlanRepository,
    ) -> None:
        self._session = session
        self._subscription_repository = subscription_repository
        self._plan_repository = plan_repository

    async def create_initial_subscription(
        self,
        organization_id: UUID,
        *,
        plan_key: PlanKey = PlanKey.FREE,
        billing_interval: BillingInterval = BillingInterval.MONTHLY,
    ) -> OrganizationSubscription:
        """Create the default FREE/ACTIVE/NONE subscription (no commit)."""
        now = _utc_now()
        subscription = OrganizationSubscription(
            organization_id=organization_id,
            provider=SubscriptionProvider.NONE.value,
            provider_customer_id=None,
            provider_subscription_id=None,
            plan_key=plan_key.value,
            status=SubscriptionStatus.ACTIVE.value,
            billing_interval=billing_interval.value,
            current_period_start=now,
            current_period_end=period_end_for_interval(now, billing_interval),
            cancel_at_period_end=False,
            canceled_at=None,
        )
        subscription = await self._subscription_repository.create(subscription)
        await self.synchronize_organization_plan(organization_id)
        return subscription

    async def get_subscription(
        self,
        organization_id: UUID,
    ) -> OrganizationSubscription:
        subscription = await self._subscription_repository.get_by_organization_id(
            organization_id,
        )
        if subscription is None:
            raise OrganizationSubscriptionNotFoundError(
                "Organization subscription was not found",
            )
        return subscription

    async def get_subscription_response(
        self,
        organization_id: UUID,
    ) -> OrganizationSubscriptionResponse:
        subscription = await self.get_subscription(organization_id)
        return OrganizationSubscriptionResponse(
            plan=subscription.plan_key,
            status=subscription.status,
            provider=subscription.provider,
            billing_interval=subscription.billing_interval,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )

    async def activate_subscription(
        self,
        organization_id: UUID,
        *,
        plan_key: PlanKey | None = None,
        billing_interval: BillingInterval | None = None,
        commit: bool = True,
    ) -> OrganizationSubscription:
        subscription = await self._require_locked_subscription(organization_id)
        now = _utc_now()
        if plan_key is not None:
            subscription.plan_key = plan_key.value
        if billing_interval is not None:
            subscription.billing_interval = billing_interval.value
        interval = BillingInterval(subscription.billing_interval)
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.cancel_at_period_end = False
        subscription.canceled_at = None
        subscription.current_period_start = now
        subscription.current_period_end = period_end_for_interval(now, interval)
        await self._session.flush()
        await self.synchronize_organization_plan(organization_id)
        if commit:
            await self._session.commit()
            await self._session.refresh(subscription)
        return subscription

    async def cancel_subscription(
        self,
        organization_id: UUID,
        *,
        at_period_end: bool = True,
        commit: bool = True,
    ) -> OrganizationSubscription:
        subscription = await self._require_locked_subscription(organization_id)
        now = _utc_now()
        if at_period_end:
            subscription.cancel_at_period_end = True
            subscription.canceled_at = now
            # Status remains ACTIVE until period ends; expire_subscription finalizes.
        else:
            subscription.status = SubscriptionStatus.CANCELED.value
            subscription.cancel_at_period_end = False
            subscription.canceled_at = now
        await self._session.flush()
        await self.synchronize_organization_plan(organization_id)
        if commit:
            await self._session.commit()
            await self._session.refresh(subscription)
        return subscription

    async def expire_subscription(
        self,
        organization_id: UUID,
        *,
        commit: bool = True,
    ) -> OrganizationSubscription:
        subscription = await self._require_locked_subscription(organization_id)
        subscription.status = SubscriptionStatus.EXPIRED.value
        subscription.cancel_at_period_end = False
        if subscription.canceled_at is None:
            subscription.canceled_at = _utc_now()
        # Expired commercial state falls back to Free entitlements.
        subscription.plan_key = PlanKey.FREE.value
        await self._session.flush()
        await self.synchronize_organization_plan(organization_id)
        if commit:
            await self._session.commit()
            await self._session.refresh(subscription)
        return subscription

    async def change_plan(
        self,
        organization_id: UUID,
        plan_key: PlanKey,
        *,
        billing_interval: BillingInterval | None = None,
        commit: bool = True,
    ) -> OrganizationSubscription:
        subscription = await self._require_locked_subscription(organization_id)
        if subscription.status not in {
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIALING.value,
            SubscriptionStatus.PAST_DUE.value,
        }:
            raise InvalidSubscriptionStateError(
                "Plan can only be changed for an active or trialing subscription",
            )
        subscription.plan_key = plan_key.value
        if billing_interval is not None:
            subscription.billing_interval = billing_interval.value
        await self._session.flush()
        await self.synchronize_organization_plan(organization_id)
        if commit:
            await self._session.commit()
            await self._session.refresh(subscription)
        return subscription

    async def synchronize_organization_plan(self, organization_id: UUID) -> OrganizationPlan:
        """Keep OrganizationPlan.plan_key aligned with the subscription plan.

        Entitlements continue to read OrganizationPlan; this is the only sync path.
        """
        subscription = await self._subscription_repository.get_by_organization_id(
            organization_id,
        )
        if subscription is None:
            raise OrganizationSubscriptionNotFoundError(
                "Organization subscription was not found",
            )

        # Validate plan key; unknown values must not silently grant paid entitlements.
        effective_plan = parse_plan_key(subscription.plan_key)

        plan = await self._plan_repository.get_by_organization_id(organization_id)
        if plan is None:
            plan = await self._plan_repository.create(
                OrganizationPlan(
                    organization_id=organization_id,
                    plan_key=effective_plan.value,
                )
            )
        elif plan.plan_key != effective_plan.value:
            plan.plan_key = effective_plan.value
            await self._session.flush()
            await self._session.refresh(plan)
        return plan

    async def _require_locked_subscription(
        self,
        organization_id: UUID,
    ) -> OrganizationSubscription:
        subscription = await self._subscription_repository.get_by_organization_id_for_update(
            organization_id,
        )
        if subscription is None:
            raise OrganizationSubscriptionNotFoundError(
                "Organization subscription was not found",
            )
        return subscription
