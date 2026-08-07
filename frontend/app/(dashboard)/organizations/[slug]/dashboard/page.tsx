"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useOrganization } from "@/components/providers/organization-provider";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  organizationMembersPath,
  organizationSettingsPath,
  organizationBillingPath,
} from "@/lib/organizations/paths";
import { organizationKeys } from "@/lib/query-keys";
import { cn } from "@/lib/utils";
import { leaveOrganization } from "@/services/memberships";
import { listOrganizations } from "@/services/organizations";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { setLastSelectedOrganizationSlug } from "@/lib/organizations/active-organization";
import { resolveInitialOrganizationSlug } from "@/lib/organizations/active-organization";
import { organizationHomePath } from "@/lib/organizations/paths";

function DashboardContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const { organization, slug, profile, plan } = useOrganization();
  const [error, setError] = useState<string | null>(null);
  const verifiedMessage =
    searchParams.get("verified") === "1"
      ? "Email verified successfully. Your account is ready."
      : null;

  const leaveMutation = useMutation({
    mutationFn: () => leaveOrganization(organization!.id),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({ queryKey: organizationKeys.list() });
      const organizations = await listOrganizations();
      if (organizations.length === 0) {
        router.replace("/onboarding");
        return;
      }
      const nextSlug = resolveInitialOrganizationSlug(organizations);
      if (nextSlug) {
        setLastSelectedOrganizationSlug(nextSlug);
        router.replace(organizationHomePath(nextSlug));
        return;
      }
      router.replace("/onboarding");
    },
    onError: (leaveError: Error) => {
      setError(leaveError.message);
    },
  });

  function handleLeave() {
    if (!organization) {
      return;
    }
    const confirmed = window.confirm(
      `Leave ${organization.name}?\n\nYou will lose access to this organization.`,
    );
    if (!confirmed) {
      return;
    }
    leaveMutation.mutate();
  }

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Welcome</CardTitle>
          <CardDescription>
            Organization workspace for {organization?.name}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {verifiedMessage ? (
            <p className="text-muted-foreground text-sm" role="status">
              {verifiedMessage}
            </p>
          ) : null}

          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Organization</p>
            <p className="font-medium">{organization?.name ?? "—"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Role</p>
            <p className="font-medium capitalize">{organization?.role ?? "—"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Plan</p>
            <p className="font-medium capitalize">{plan?.plan ?? "—"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Website</p>
            <p className="font-medium">{profile?.website ?? "—"}</p>
          </div>

          {error ? (
            <p className="text-destructive text-sm" role="alert">
              {error}
            </p>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <Link
              href={organizationMembersPath(slug)}
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Members
            </Link>
            <Link
              href={organizationSettingsPath(slug)}
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Settings
            </Link>
            <Link
              href={organizationBillingPath(slug)}
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Billing
            </Link>
            <Button
              variant="outline"
              onClick={handleLeave}
              disabled={!organization || leaveMutation.isPending}
            >
              {leaveMutation.isPending ? "Leaving..." : "Leave organization"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}

export default function OrganizationDashboardPage() {
  return (
    <Suspense
      fallback={
        <main className="flex flex-1 items-center justify-center px-6 py-16">
          <p className="text-muted-foreground text-sm">Loading dashboard...</p>
        </main>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
