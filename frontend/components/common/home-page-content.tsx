"use client";

import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { APP_NAME } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";

export function HomePageContent() {
  const session = useAuthStore((state) => state.session);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-24">
      <div className="flex w-full max-w-xl flex-col items-center gap-6 text-center">
        <div className="space-y-3">
          <h1 className="text-4xl font-semibold tracking-tight">{APP_NAME}</h1>
          <p className="text-muted-foreground text-lg">
            A production-ready foundation for building modern SaaS applications.
          </p>
        </div>

        <div className="flex min-h-10 flex-wrap items-center justify-center gap-3">
          {!isHydrated ? (
            <p className="text-muted-foreground text-sm">Loading...</p>
          ) : session ? (
            <Link
              href="/dashboard"
              className={cn(buttonVariants({ size: "lg" }))}
            >
              Go to Dashboard
            </Link>
          ) : (
            <>
              <Link
                href="/auth/register"
                className={cn(buttonVariants({ size: "lg" }))}
              >
                Create Account
              </Link>
              <Link
                href="/auth/login"
                className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
              >
                Sign In
              </Link>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
