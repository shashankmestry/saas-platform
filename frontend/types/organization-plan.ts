export type OrganizationPlan = {
  plan: "free" | "standard" | "premium" | "enterprise" | string;
  features: Record<string, boolean>;
  limits: Record<string, number | null>;
  usage: Record<string, number>;
};
