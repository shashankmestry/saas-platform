"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { buildLoginPath, buildRegisterPath } from "@/lib/auth/return-path";
import { cn } from "@/lib/utils";
import { acceptInvitation } from "@/services/memberships";
import { useAuthStore } from "@/store/auth";

// Survives React Strict Mode remounts so accept is not double-fired in development.
const acceptAttempts = new Map<string, Promise<void>>();

function AcceptInvitationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const session = useAuthStore((state) => state.session);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "accepting" | "done" | "failed">(
    "idle",
  );

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    if (!token) {
      setError("Missing invitation token.");
      return;
    }

    if (!session) {
      const returnPath = `/invitations/accept?token=${encodeURIComponent(token)}`;
      router.replace(buildLoginPath(returnPath));
      return;
    }

    if (status === "done" || status === "failed") {
      return;
    }

    setStatus("accepting");

    let isMounted = true;

    const existingAttempt = acceptAttempts.get(token);
    const attempt =
      existingAttempt ??
      acceptInvitation(token)
        .then(() => undefined)
        .finally(() => {
          // Keep the resolved promise briefly so remounts reuse success.
          window.setTimeout(() => {
            acceptAttempts.delete(token);
          }, 5000);
        });

    if (!existingAttempt) {
      acceptAttempts.set(token, attempt);
    }

    void attempt
      .then(() => {
        if (!isMounted) {
          return;
        }
        setStatus("done");
        router.replace("/dashboard");
      })
      .catch((acceptError: unknown) => {
        if (!isMounted) {
          return;
        }
        setStatus("failed");
        setError(
          acceptError instanceof Error
            ? acceptError.message
            : "Unable to accept invitation",
        );
      });

    return () => {
      isMounted = false;
    };
  }, [isHydrated, router, session, status, token]);

  if (!isHydrated || (session && status === "accepting" && !error)) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <p className="text-muted-foreground text-sm">Accepting invitation...</p>
      </main>
    );
  }

  if (!token) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Invalid invitation</CardTitle>
            <CardDescription>
              This invitation link is missing a token.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/" className={cn(buttonVariants())}>
              Go home
            </Link>
          </CardContent>
        </Card>
      </main>
    );
  }

  if (!session) {
    const returnPath = `/invitations/accept?token=${encodeURIComponent(token)}`;
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Sign in to continue</CardTitle>
            <CardDescription>
              Sign in or create an account with the invited email to accept this
              invitation.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-3">
            <Link href={buildLoginPath(returnPath)} className={cn(buttonVariants())}>
              Sign in
            </Link>
            <Link
              href={buildRegisterPath(returnPath)}
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Create account
            </Link>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Invitation</CardTitle>
          <CardDescription>
            {error
              ? "We could not accept this invitation."
              : "Redirecting to your dashboard..."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error ? (
            <p className="text-destructive text-sm" role="alert">
              {error}
            </p>
          ) : null}
          <Link href="/dashboard" className={cn(buttonVariants({ variant: "outline" }))}>
            Go to dashboard
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}

export default function AcceptInvitationPage() {
  return (
    <Suspense
      fallback={
        <main className="flex flex-1 items-center justify-center px-6 py-16">
          <p className="text-muted-foreground text-sm">Loading invitation...</p>
        </main>
      }
    >
      <AcceptInvitationContent />
    </Suspense>
  );
}
