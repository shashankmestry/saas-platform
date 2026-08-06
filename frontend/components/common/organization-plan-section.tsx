"use client";

import { useQuery } from "@tanstack/react-query";

import { Label } from "@/components/ui/label";
import { organizationKeys } from "@/lib/query-keys";
import { getOrganizationPlan } from "@/services/organizations";

const PLAN_LABELS: Record<string, string> = {
  free: "Free",
  standard: "Standard",
  premium: "Premium",
  enterprise: "Enterprise",
};

const FEATURE_LABELS: Record<string, string> = {
  "analytics.basic": "Basic Analytics",
  "analytics.advanced": "Advanced Analytics",
  "support.priority": "Priority Support",
};

type OrganizationPlanSectionProps = {
  organizationId: string;
  enabled?: boolean;
};

export function OrganizationPlanSection({
  organizationId,
  enabled = true,
}: OrganizationPlanSectionProps) {
  const planQuery = useQuery({
    queryKey: organizationKeys.plan(organizationId),
    queryFn: () => getOrganizationPlan(organizationId),
    enabled: Boolean(organizationId) && enabled,
  });

  if (planQuery.isLoading) {
    return (
      <div className="space-y-2 border-b border-border pb-4">
        <Label>Current Plan</Label>
        <p className="text-muted-foreground text-sm">Loading plan...</p>
      </div>
    );
  }

  if (planQuery.isError || !planQuery.data) {
    return (
      <div className="space-y-2 border-b border-border pb-4">
        <Label>Current Plan</Label>
        <p className="text-destructive text-sm" role="alert">
          {planQuery.error instanceof Error
            ? planQuery.error.message
            : "Unable to load plan"}
        </p>
      </div>
    );
  }

  const plan = planQuery.data;
  const planLabel = PLAN_LABELS[plan.plan] ?? plan.plan;
  const memberLimit = plan.limits["organization.members"];
  const memberUsage = plan.usage["organization.members"] ?? 0;
  const seatLabel =
    memberLimit === null || memberLimit === undefined
      ? `${memberUsage} of Unlimited`
      : `${memberUsage} of ${memberLimit} used`;

  return (
    <div className="space-y-3 border-b border-border pb-4">
      <div className="space-y-1">
        <Label>Current Plan</Label>
        <p className="font-medium">{planLabel}</p>
      </div>

      <div className="space-y-1">
        <p className="text-muted-foreground text-sm">Member Seats</p>
        <p className="text-sm">{seatLabel}</p>
      </div>

      <div className="space-y-1">
        <p className="text-muted-foreground text-sm">Entitlements</p>
        <ul className="space-y-1 text-sm">
          {Object.entries(FEATURE_LABELS).map(([key, label]) => {
            const enabledFeature = Boolean(plan.features[key]);
            return (
              <li key={key} className="flex items-center gap-2">
                <span aria-hidden="true">{enabledFeature ? "✓" : "–"}</span>
                <span className={enabledFeature ? undefined : "text-muted-foreground"}>
                  {label}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
