"""Code-defined organization roles, permissions, and role → permission mapping.

Roles and permissions are intentionally not stored in the database.
Membership rows continue to store role values as plain strings that must
match OrganizationRole values.
"""

from enum import StrEnum


class OrganizationRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class OrganizationPermission(StrEnum):
    ORGANIZATION_VIEW = "organization.view"
    ORGANIZATION_MANAGE = "organization.manage"
    ORGANIZATION_OWNERSHIP_TRANSFER = "organization.ownership.transfer"

    MEMBER_VIEW = "member.view"
    MEMBER_INVITE = "member.invite"
    MEMBER_REMOVE = "member.remove"
    MEMBER_ROLE_UPDATE = "member.role.update"

    INVITATION_VIEW = "invitation.view"
    INVITATION_CREATE = "invitation.create"
    INVITATION_REVOKE = "invitation.revoke"


ROLE_PERMISSIONS: dict[OrganizationRole, frozenset[OrganizationPermission]] = {
    OrganizationRole.OWNER: frozenset(
        {
            OrganizationPermission.ORGANIZATION_VIEW,
            OrganizationPermission.ORGANIZATION_MANAGE,
            OrganizationPermission.ORGANIZATION_OWNERSHIP_TRANSFER,
            OrganizationPermission.MEMBER_VIEW,
            OrganizationPermission.MEMBER_INVITE,
            OrganizationPermission.MEMBER_REMOVE,
            OrganizationPermission.MEMBER_ROLE_UPDATE,
            OrganizationPermission.INVITATION_VIEW,
            OrganizationPermission.INVITATION_CREATE,
            OrganizationPermission.INVITATION_REVOKE,
        }
    ),
    OrganizationRole.MEMBER: frozenset(
        {
            OrganizationPermission.ORGANIZATION_VIEW,
            OrganizationPermission.MEMBER_VIEW,
        }
    ),
}


def parse_organization_role(value: str) -> OrganizationRole:
    """Parse a stored membership role string into OrganizationRole."""
    try:
        return OrganizationRole(value)
    except ValueError as exc:
        raise ValueError(f"Unknown organization role: {value}") from exc


def permissions_for_role(role: OrganizationRole) -> frozenset[OrganizationPermission]:
    return ROLE_PERMISSIONS.get(role, frozenset())


def role_has_permission(
    role: OrganizationRole,
    permission: OrganizationPermission,
) -> bool:
    return permission in permissions_for_role(role)
