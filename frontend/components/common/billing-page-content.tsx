"use client";

import { useOrganization } from "@/components/providers/organization-provider";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { OrganizationPermission } from "@/lib/auth/permissions";

const PLAN_LABELS: Record<string, string> = {
  free: "Free",
  standard: "Standard",
  premium: "Premium",
  enterprise: "Enterprise",
};

const STATUS_LABELS: Record<string, string> = {
  trialing: "Trialing",
  active: "Active",
  past_due: "Past due",
  canceled: "Canceled",
  expired: "Expired",
  incomplete: "Incomplete",
};

const INTERVAL_LABELS: Record<string, string> = {
  monthly: "Monthly",
  yearly: "Yearly",
};

const PROVIDER_LABELS: Record<string, string> = {
  none: "None",
  stripe: "Stripe",
  paddle: "Paddle",
  razorpay: "Razorpay",
};

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function BillingPageContent() {
  const { organization, subscription, can, isLoading } = useOrganization();
  const canView = can(OrganizationPermission.ORGANIZATION_VIEW);

  if (isLoading) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <p className="text-muted-foreground text-sm">Loading billing...</p>
      </main>
    );
  }

  if (!canView || !organization) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle>Billing</CardTitle>
            <CardDescription>
              You do not have permission to view billing for this organization.
            </CardDescription>
          </CardHeader>
        </Card>
      </main>
    );
  }

  if (!subscription) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle>Billing</CardTitle>
            <CardDescription>Unable to load subscription details.</CardDescription>
          </CardHeader>
        </Card>
      </main>
    );
  }

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Billing</CardTitle>
          <CardDescription>
            Read-only subscription details for {organization.name}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Current Plan</p>
            <p className="font-medium">
              {PLAN_LABELS[subscription.plan] ?? subscription.plan}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Subscription Status</p>
            <p className="font-medium">
              {STATUS_LABELS[subscription.status] ?? subscription.status}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Billing Interval</p>
            <p className="font-medium">
              {INTERVAL_LABELS[subscription.billing_interval] ??
                subscription.billing_interval}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Current Period</p>
            <p className="text-sm">
              {formatDate(subscription.current_period_start)} —{" "}
              {formatDate(subscription.current_period_end)}
            </p>
            {subscription.cancel_at_period_end ? (
              <p className="text-muted-foreground text-xs">
                Cancellation scheduled at period end.
              </p>
            ) : null}
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Provider</p>
            <p className="font-medium">
              {PROVIDER_LABELS[subscription.provider] ?? subscription.provider}
            </p>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
