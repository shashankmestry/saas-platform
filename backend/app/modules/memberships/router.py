from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.authorization import OrganizationPermission
from app.modules.auth.dependencies import get_current_user
from app.modules.memberships.authorization import require_organization_permission
from app.modules.memberships.context import OrganizationContext
from app.modules.memberships.dependencies import get_membership_service
from app.modules.memberships.exceptions import (
    AlreadyOrganizationMemberError,
    InvalidMembershipOperationError,
    InvitationAlreadyAcceptedError,
    InvitationEmailMismatchError,
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationNotPendingError,
    InvitationRevokedError,
    LastOwnerInvariantError,
    MembershipNotFoundError,
    PendingInvitationExistsError,
)
from app.modules.memberships.schemas import (
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
    MemberRoleUpdate,
    OrganizationMemberResponse,
    OwnershipTransferRequest,
)
from app.modules.memberships.service import MembershipService
from app.modules.users.models import User

organization_memberships_router = APIRouter()
invitations_router = APIRouter()


def _conflict(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@organization_memberships_router.get(
    "/{organization_id}/members",
    response_model=list[OrganizationMemberResponse],
    summary="List organization members",
)
async def list_organization_members(
    organization_context: Annotated[
        OrganizationContext,
        Depends(require_organization_permission(OrganizationPermission.MEMBER_VIEW)),
    ],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> list[OrganizationMemberResponse]:
    return await membership_service.list_members(organization_context.organization_id)


@organization_memberships_router.patch(
    "/{organization_id}/members/{membership_id}",
    response_model=OrganizationMemberResponse,
    summary="Update a member role",
)
async def update_member_role(
    membership_id: UUID,
    payload: MemberRoleUpdate,
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(OrganizationPermission.MEMBER_ROLE_UPDATE)
        ),
    ],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> OrganizationMemberResponse:
    try:
        membership = await membership_service.update_member_role(
            organization_id=organization_context.organization_id,
            membership_id=membership_id,
            new_role=payload.role,
        )
    except MembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LastOwnerInvariantError as exc:
        raise _conflict(exc) from exc

    members = await membership_service.list_members(organization_context.organization_id)
    for member in members:
        if member.id == membership.id:
            return member

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Membership not found",
    )


@organization_memberships_router.delete(
    "/{organization_id}/members/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member",
)
async def remove_member(
    membership_id: UUID,
    organization_context: Annotated[
        OrganizationContext,
        Depends(require_organization_permission(OrganizationPermission.MEMBER_REMOVE)),
    ],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> Response:
    try:
        await membership_service.remove_member(
            organization_id=organization_context.organization_id,
            membership_id=membership_id,
        )
    except MembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LastOwnerInvariantError as exc:
        raise _conflict(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@organization_memberships_router.post(
    "/{organization_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave the organization",
)
async def leave_organization(
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(OrganizationPermission.ORGANIZATION_VIEW)
        ),
    ],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> Response:
    try:
        await membership_service.leave_organization(
            organization_id=organization_context.organization_id,
            user=organization_context.user,
        )
    except MembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LastOwnerInvariantError as exc:
        raise _conflict(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@organization_memberships_router.post(
    "/{organization_id}/ownership/transfer",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Transfer organization ownership",
)
async def transfer_ownership(
    payload: OwnershipTransferRequest,
    organization_context: Annotated[
        OrganizationContext,
        Depends(
            require_organization_permission(
                OrganizationPermission.ORGANIZATION_OWNERSHIP_TRANSFER
            )
        ),
    ],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> Response:
    try:
        await membership_service.transfer_ownership(
            organization_id=organization_context.organization_id,
            current_user=organization_context.user,
            target_membership_id=payload.membership_id,
        )
    except MembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidMembershipOperationError as exc:
        raise _conflict(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@organization_memberships_router.get(
    "/{organization_id}/invitations",
    response_model=list[InvitationResponse],
    summary="List pending organization invitations",
)
async def list_organization_invitations(
    organization_context: Annotated[
        OrganizationContext,
        Depends(require_organization_permission(OrganizationPermission.INVITATION_VIEW)),
    ],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> list[InvitationResponse]:
    invitations = await membership_service.list_pending_invitations(
        organization_context.organization_id,
    )
    return [
        InvitationResponse.model_validate(invitation) for invitation in invitations
    ]


@organization_memberships_router.post(
    "/{organization_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an organization invitation",
)
async def create_organization_invitation(
    payload: InvitationCreate,
    organization_context: Annotated[
        OrganizationContext,
        Depends(require_organization_permission(OrganizationPermission.MEMBER_INVITE)),
    ],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> InvitationResponse:
    try:
        invitation, invite_url = await membership_service.create_invitation(
            organization_context.organization_id,
            organization_context.user,
            payload.email,
        )
    except AlreadyOrganizationMemberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except PendingInvitationExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    response = InvitationResponse.model_validate(invitation)
    response.invite_url = invite_url
    return response


@organization_memberships_router.delete(
    "/{organization_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a pending organization invitation",
)
async def revoke_organization_invitation(
    invitation_id: UUID,
    organization_context: Annotated[
        OrganizationContext,
        Depends(require_organization_permission(OrganizationPermission.INVITATION_REVOKE)),
    ],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> Response:
    try:
        await membership_service.revoke_invitation(
            organization_context.organization_id,
            invitation_id,
        )
    except InvitationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvitationNotPendingError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@invitations_router.post(
    "/accept",
    response_model=InvitationResponse,
    summary="Accept an organization invitation",
)
async def accept_invitation(
    payload: InvitationAccept,
    current_user: Annotated[User, Depends(get_current_user)],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> InvitationResponse:
    try:
        invitation = await membership_service.accept_invitation(
            current_user,
            payload.token,
        )
    except InvitationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvitationAlreadyAcceptedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvitationRevokedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvitationExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(exc),
        ) from exc
    except InvitationEmailMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except AlreadyOrganizationMemberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return InvitationResponse.model_validate(invitation)
