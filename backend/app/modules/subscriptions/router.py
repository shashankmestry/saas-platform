from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.authorization import OrganizationPermission
from app.modules.memberships.authorization import require_organization_permission
from app.modules.memberships.context import OrganizationContext
from app.modules.subscriptions.dependencies import get_subscription_service
from app.modules.subscriptions.exceptions import OrganizationSubscriptionNotFoundError
from app.modules.subscriptions.schemas import OrganizationSubscriptionResponse
from app.modules.subscriptions.service import SubscriptionService

router = APIRouter()


@router.get(
    "/{organization_id}/subscription",
    response_model=OrganizationSubscriptionResponse,
    summary="Get organization subscription",
)
async def get_organization_subscription(
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(OrganizationPermission.ORGANIZATION_VIEW)
        ),
    ],
    subscription_service: Annotated[
        SubscriptionService,
        Depends(get_subscription_service),
    ],
) -> OrganizationSubscriptionResponse:
    try:
        return await subscription_service.get_subscription_response(
            organization_context.organization_id,
        )
    except OrganizationSubscriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
