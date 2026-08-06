export const organizationKeys = {
  all: ["organizations"] as const,
  list: () => [...organizationKeys.all, "list"] as const,
  profile: (organizationId: string) =>
    [...organizationKeys.all, "profile", organizationId] as const,
};

export const membershipKeys = {
  all: ["memberships"] as const,
  members: (organizationId: string) =>
    [...membershipKeys.all, "members", organizationId] as const,
  invitations: (organizationId: string) =>
    [...membershipKeys.all, "invitations", organizationId] as const,
};
