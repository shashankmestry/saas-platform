"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { fetchCurrentUser, logout } from "@/services/auth";
import { useAuthStore } from "@/store/auth";

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const session = useAuthStore((state) => state.session);
  const user = useAuthStore((state) => state.user);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const setUser = useAuthStore((state) => state.setUser);
  const clear = useAuthStore((state) => state.clear);
  const [error, setError] = useState<string | null>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [verifiedMessage, setVerifiedMessage] = useState<string | null>(null);

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

    if (user) {
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
  }, [isHydrated, router, session, setUser, user]);

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

  if (!isHydrated || (session && !user && !error)) {
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

          <Button
            variant="outline"
            onClick={handleLogout}
            disabled={isLoggingOut}
          >
            {isLoggingOut ? "Signing out..." : "Logout"}
          </Button>
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
