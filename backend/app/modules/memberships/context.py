from dataclasses import dataclass
from uuid import UUID

from app.core.authorization import (
    OrganizationPermission,
    OrganizationRole,
    parse_organization_role,
    permissions_for_role,
    role_has_permission,
)
from app.modules.memberships.models import OrganizationMembership
from app.modules.organizations.models import Organization
from app.modules.users.models import User


@dataclass(frozen=True, slots=True)
class OrganizationContext:
    """Authorized access context for one organization + membership."""

    user: User
    organization: Organization
    membership: OrganizationMembership
    role: OrganizationRole
    permissions: frozenset[OrganizationPermission]

    @classmethod
    def from_membership(
        cls,
        *,
        user: User,
        organization: Organization,
        membership: OrganizationMembership,
    ) -> "OrganizationContext":
        role = parse_organization_role(membership.role)
        return cls(
            user=user,
            organization=organization,
            membership=membership,
            role=role,
            permissions=permissions_for_role(role),
        )

    @property
    def organization_id(self) -> UUID:
        return self.organization.id

    def can(self, permission: OrganizationPermission) -> bool:
        return role_has_permission(self.role, permission)

    def permission_values(self) -> list[str]:
        return sorted(permission.value for permission in self.permissions)
