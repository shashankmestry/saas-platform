export const OrganizationRole = {
  OWNER: "owner",
  MEMBER: "member",
} as const;

export type OrganizationRole =
  (typeof OrganizationRole)[keyof typeof OrganizationRole];

export const OrganizationPermission = {
  ORGANIZATION_VIEW: "organization.view",
  ORGANIZATION_MANAGE: "organization.manage",
  ORGANIZATION_OWNERSHIP_TRANSFER: "organization.ownership.transfer",
  MEMBER_VIEW: "member.view",
  MEMBER_INVITE: "member.invite",
  MEMBER_REMOVE: "member.remove",
  MEMBER_ROLE_UPDATE: "member.role.update",
  INVITATION_VIEW: "invitation.view",
  INVITATION_CREATE: "invitation.create",
  INVITATION_REVOKE: "invitation.revoke",
} as const;

export type OrganizationPermission =
  (typeof OrganizationPermission)[keyof typeof OrganizationPermission];

export function can(
  permissions: readonly string[] | null | undefined,
  permission: OrganizationPermission | string,
): boolean {
  if (!permissions || permissions.length === 0) {
    return false;
  }

  return permissions.includes(permission);
}
