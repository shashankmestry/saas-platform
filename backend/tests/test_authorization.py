"""Unit tests for code-defined organization RBAC."""

from app.core.authorization import (
    OrganizationPermission,
    OrganizationRole,
    permissions_for_role,
    role_has_permission,
)


def test_owner_permissions() -> None:
    permissions = permissions_for_role(OrganizationRole.OWNER)

    assert OrganizationPermission.ORGANIZATION_VIEW in permissions
    assert OrganizationPermission.ORGANIZATION_MANAGE in permissions
    assert OrganizationPermission.ORGANIZATION_OWNERSHIP_TRANSFER in permissions
    assert OrganizationPermission.MEMBER_VIEW in permissions
    assert OrganizationPermission.MEMBER_INVITE in permissions
    assert OrganizationPermission.MEMBER_REMOVE in permissions
    assert OrganizationPermission.MEMBER_ROLE_UPDATE in permissions
    assert OrganizationPermission.INVITATION_VIEW in permissions
    assert OrganizationPermission.INVITATION_CREATE in permissions
    assert OrganizationPermission.INVITATION_REVOKE in permissions


def test_member_permissions() -> None:
    permissions = permissions_for_role(OrganizationRole.MEMBER)

    assert OrganizationPermission.ORGANIZATION_VIEW in permissions
    assert OrganizationPermission.MEMBER_VIEW in permissions
    assert OrganizationPermission.ORGANIZATION_MANAGE not in permissions
    assert OrganizationPermission.MEMBER_INVITE not in permissions
    assert OrganizationPermission.INVITATION_CREATE not in permissions
    assert OrganizationPermission.INVITATION_REVOKE not in permissions
    assert OrganizationPermission.INVITATION_VIEW not in permissions


def test_role_has_permission_helpers() -> None:
    assert role_has_permission(
        OrganizationRole.OWNER,
        OrganizationPermission.MEMBER_INVITE,
    )
    assert not role_has_permission(
        OrganizationRole.MEMBER,
        OrganizationPermission.MEMBER_INVITE,
    )
    assert role_has_permission(
        OrganizationRole.MEMBER,
        OrganizationPermission.MEMBER_VIEW,
    )
