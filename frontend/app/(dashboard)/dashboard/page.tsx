"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { organizationKeys } from "@/lib/query-keys";
import { cn } from "@/lib/utils";
import { fetchCurrentUser, logout } from "@/services/auth";
import { leaveOrganization } from "@/services/memberships";
import { listOrganizations } from "@/services/organizations";
import { useAuthStore } from "@/store/auth";

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const session = useAuthStore((state) => state.session);
  const user = useAuthStore((state) => state.user);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const setUser = useAuthStore((state) => state.setUser);
  const clear = useAuthStore((state) => state.clear);
  const [error, setError] = useState<string | null>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [verifiedMessage, setVerifiedMessage] = useState<string | null>(null);

  const organizationsQuery = useQuery({
    queryKey: organizationKeys.list(),
    queryFn: listOrganizations,
    enabled: isHydrated && Boolean(session),
  });

  const organization = organizationsQuery.data?.[0] ?? null;

  useEffect(() => {
    if (searchParams.get("verified") === "1") {
      setVerifiedMessage("Email verified successfully. Your account is ready.");
    }
  }, [searchParams]);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    if (!session) {
      router.replace("/auth/login");
      return;
    }

    if (organizationsQuery.isSuccess && (organizationsQuery.data?.length ?? 0) === 0) {
      router.replace("/onboarding");
    }
  }, [
    isHydrated,
    organizationsQuery.data,
    organizationsQuery.isSuccess,
    router,
    session,
  ]);

  useEffect(() => {
    if (!isHydrated || !session || user) {
      return;
    }

    let isMounted = true;

    async function loadUser() {
      try {
        const platformUser = await fetchCurrentUser();
        if (isMounted) {
          setUser(platformUser);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load platform user",
          );
        }
      }
    }

    void loadUser();

    return () => {
      isMounted = false;
    };
  }, [isHydrated, session, setUser, user]);

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
      router.refresh();
    },
    onError: (leaveError: Error) => {
      setError(leaveError.message);
    },
  });

  async function handleLogout() {
    setIsLoggingOut(true);
    setError(null);

    try {
      await logout();
      clear();
      router.replace("/");
    } catch (logoutError) {
      setError(
        logoutError instanceof Error ? logoutError.message : "Unable to log out",
      );
      setIsLoggingOut(false);
    }
  }

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

  if (
    !isHydrated ||
    (session && organizationsQuery.isLoading && !error)
  ) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <p className="text-muted-foreground text-sm">Loading dashboard...</p>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Welcome</CardTitle>
          <CardDescription>Temporary dashboard for authentication.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {verifiedMessage ? (
            <p className="text-sm text-muted-foreground" role="status">
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
            <p className="text-muted-foreground text-sm">Email</p>
            <p className="font-medium">{user?.email ?? session.user.email}</p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground text-sm">Platform User ID</p>
            <p className="font-mono text-sm break-all">{user?.id ?? "—"}</p>
          </div>

          {error ? (
            <p className="text-destructive text-sm" role="alert">
              {error}
            </p>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <Link
              href="/dashboard/members"
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Members
            </Link>
            <Link
              href="/dashboard/settings/organization"
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Organization settings
            </Link>
            <Button
              variant="outline"
              onClick={handleLeave}
              disabled={!organization || leaveMutation.isPending}
            >
              {leaveMutation.isPending ? "Leaving..." : "Leave organization"}
            </Button>
            <Button
              variant="outline"
              onClick={handleLogout}
              disabled={isLoggingOut}
            >
              {isLoggingOut ? "Signing out..." : "Logout"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}

export default function DashboardPage() {
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
