from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import (
    Feature,
    Limit,
    PlanKey,
    entitlements_for_plan,
    parse_plan_key,
    plan_get_limit,
    plan_has_feature,
)
from app.modules.memberships.repository import InvitationRepository, MembershipRepository
from app.modules.plans.exceptions import (
    OrganizationPlanNotFoundError,
    UnknownOrganizationPlanError,
)
from app.modules.plans.models import OrganizationPlan
from app.modules.plans.repository import OrganizationPlanRepository
from app.modules.plans.schemas import OrganizationPlanResponse


class PlanService:
    """Resolves organization plan assignments against code-defined entitlements."""

    def __init__(
        self,
        session: AsyncSession,
        plan_repository: OrganizationPlanRepository,
        membership_repository: MembershipRepository,
        invitation_repository: InvitationRepository,
    ) -> None:
        self._session = session
        self._plan_repository = plan_repository
        self._membership_repository = membership_repository
        self._invitation_repository = invitation_repository

    async def get_organization_plan_row(
        self,
        organization_id: UUID,
        *,
        for_update: bool = False,
    ) -> OrganizationPlan:
        if for_update:
            row = await self._plan_repository.get_by_organization_id_for_update(
                organization_id,
            )
        else:
            row = await self._plan_repository.get_by_organization_id(organization_id)
        if row is None:
            raise OrganizationPlanNotFoundError(
                "Organization plan assignment was not found",
            )
        return row

    def resolve_plan_key(self, plan_key: str) -> PlanKey:
        try:
            return parse_plan_key(plan_key)
        except ValueError as exc:
            raise UnknownOrganizationPlanError(str(exc)) from exc

    async def get_organization_plan_key(self, organization_id: UUID) -> PlanKey:
        row = await self.get_organization_plan_row(organization_id)
        return self.resolve_plan_key(row.plan_key)

    async def get_entitlements(self, organization_id: UUID):
        plan = await self.get_organization_plan_key(organization_id)
        return entitlements_for_plan(plan)

    async def has_feature(self, organization_id: UUID, feature: Feature) -> bool:
        plan = await self.get_organization_plan_key(organization_id)
        return plan_has_feature(plan, feature)

    async def get_limit(self, organization_id: UUID, limit: Limit) -> int | None:
        """Return the numeric limit for the organization, or None if unlimited."""
        plan = await self.get_organization_plan_key(organization_id)
        return plan_get_limit(plan, limit)

    async def count_member_seats(self, organization_id: UUID) -> int:
        """Seat usage = active memberships + active pending invitations."""
        members = await self._membership_repository.count_members(organization_id)
        pending = await self._invitation_repository.count_pending(organization_id)
        return members + pending

    async def get_organization_plan_response(
        self,
        organization_id: UUID,
    ) -> OrganizationPlanResponse:
        plan = await self.get_organization_plan_key(organization_id)
        entitlements = entitlements_for_plan(plan)
        seat_usage = await self.count_member_seats(organization_id)
        return OrganizationPlanResponse(
            plan=plan.value,
            features={feature.value: enabled for feature, enabled in entitlements.features.items()},
            limits={limit.value: value for limit, value in entitlements.limits.items()},
            usage={Limit.ORGANIZATION_MEMBERS.value: seat_usage},
        )
