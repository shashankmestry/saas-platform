export const organizationKeys = {
  all: ["organizations"] as const,
  list: () => [...organizationKeys.all, "list"] as const,
  detail: (organizationId: string) =>
    [...organizationKeys.all, "detail", organizationId] as const,
  profile: (organizationId: string) =>
    ["profile", organizationId] as const,
  plan: (organizationId: string) => ["plan", organizationId] as const,
  subscription: (organizationId: string) =>
    ["subscription", organizationId] as const,
};

export const membershipKeys = {
  all: ["memberships"] as const,
  members: (organizationId: string) =>
    ["members", organizationId] as const,
  invitations: (organizationId: string) =>
    ["invitations", organizationId] as const,
};
