from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.authorization import OrganizationPermission
from app.modules.memberships.authorization import require_organization_permission
from app.modules.memberships.context import OrganizationContext
from app.modules.plans.dependencies import get_plan_service
from app.modules.plans.exceptions import (
    OrganizationPlanNotFoundError,
    UnknownOrganizationPlanError,
)
from app.modules.plans.schemas import OrganizationPlanResponse
from app.modules.plans.service import PlanService

router = APIRouter()


@router.get(
    "/{organization_id}/plan",
    response_model=OrganizationPlanResponse,
    summary="Get organization plan and entitlements",
)
async def get_organization_plan(
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(OrganizationPermission.ORGANIZATION_VIEW)
        ),
    ],
    plan_service: Annotated[PlanService, Depends(get_plan_service)],
) -> OrganizationPlanResponse:
    try:
        return await plan_service.get_organization_plan_response(
            organization_context.organization_id,
        )
    except OrganizationPlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UnknownOrganizationPlanError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Organization plan configuration is invalid",
        ) from exc
