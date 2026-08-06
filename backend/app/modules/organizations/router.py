from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.authorization import OrganizationPermission
from app.modules.auth.dependencies import get_current_user
from app.modules.memberships.authorization import require_organization_permission
from app.modules.memberships.context import OrganizationContext
from app.modules.organizations.dependencies import get_organization_service
from app.modules.organizations.exceptions import (
    LogoObjectMissingError,
    LogoStorageOperationError,
    LogoValidationError,
    OrganizationSlugConflictError,
)
from app.modules.organizations.schemas import (
    LogoConfirmRequest,
    LogoUploadRequest,
    LogoUploadResponse,
    OrganizationCreate,
    OrganizationProfileResponse,
    OrganizationProfileUpdate,
    OrganizationResponse,
)
from app.modules.organizations.service import OrganizationService
from app.modules.users.models import User

router = APIRouter()


@router.get(
    "",
    response_model=list[OrganizationResponse],
    summary="List organizations for the current user",
)
async def list_organizations(
    current_user: Annotated[User, Depends(get_current_user)],
    organization_service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> list[OrganizationResponse]:
    return await organization_service.list_for_user(current_user)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an organization",
)
async def create_organization(
    payload: OrganizationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    organization_service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> OrganizationResponse:
    try:
        return await organization_service.create_organization(
            current_user,
            payload.name,
        )
    except OrganizationSlugConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{organization_id}/profile",
    response_model=OrganizationProfileResponse,
    summary="Get organization profile",
)
async def get_organization_profile(
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(OrganizationPermission.ORGANIZATION_VIEW)
        ),
    ],
    organization_service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> OrganizationProfileResponse:
    return await organization_service.get_profile(organization_context.organization)


@router.patch(
    "/{organization_id}/profile",
    response_model=OrganizationProfileResponse,
    summary="Update organization profile",
)
async def update_organization_profile(
    payload: OrganizationProfileUpdate,
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(OrganizationPermission.ORGANIZATION_MANAGE)
        ),
    ],
    organization_service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> OrganizationProfileResponse:
    return await organization_service.update_profile(
        organization_id=organization_context.organization_id,
        payload=payload,
    )


@router.post(
    "/{organization_id}/logo/upload",
    response_model=LogoUploadResponse,
    summary="Request organization logo upload authorization",
)
async def request_organization_logo_upload(
    payload: LogoUploadRequest,
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(OrganizationPermission.ORGANIZATION_MANAGE)
        ),
    ],
    organization_service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> LogoUploadResponse:
    try:
        return await organization_service.request_logo_upload(
            organization_id=organization_context.organization_id,
            payload=payload,
        )
    except LogoValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except LogoStorageOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post(
    "/{organization_id}/logo/confirm",
    response_model=OrganizationProfileResponse,
    summary="Confirm organization logo upload",
)
async def confirm_organization_logo_upload(
    payload: LogoConfirmRequest,
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(OrganizationPermission.ORGANIZATION_MANAGE)
        ),
    ],
    organization_service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> OrganizationProfileResponse:
    try:
        return await organization_service.confirm_logo_upload(
            organization_id=organization_context.organization_id,
            payload=payload,
        )
    except LogoValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except LogoObjectMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LogoStorageOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{organization_id}/logo",
    response_model=OrganizationProfileResponse,
    summary="Remove organization logo",
)
async def delete_organization_logo(
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(OrganizationPermission.ORGANIZATION_MANAGE)
        ),
    ],
    organization_service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> OrganizationProfileResponse:
    return await organization_service.delete_logo(
        organization_id=organization_context.organization_id,
    )
