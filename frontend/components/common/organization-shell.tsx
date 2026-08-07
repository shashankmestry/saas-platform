"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { OrganizationSwitcher } from "@/components/common/organization-switcher";
import { useOrganization } from "@/components/providers/organization-provider";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  organizationBillingPath,
  organizationHomePath,
  organizationMembersPath,
  organizationSettingsPath,
} from "@/lib/organizations/paths";
import { cn } from "@/lib/utils";
import { logout } from "@/services/auth";
import { useAuthStore } from "@/store/auth";

type OrganizationShellProps = {
  children: React.ReactNode;
};

export function OrganizationShell({ children }: OrganizationShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const session = useAuthStore((state) => state.session);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const clear = useAuthStore((state) => state.clear);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const {
    organization,
    slug,
    isOrganizationsLoading,
    organizationMissing,
    organizations,
  } = useOrganization();

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    if (!session) {
      router.replace("/auth/login");
    }
  }, [isHydrated, router, session]);

  useEffect(() => {
    if (isOrganizationsLoading) {
      return;
    }
    if (organizations.length === 0) {
      router.replace("/onboarding");
      return;
    }
    if (organizationMissing) {
      router.replace("/dashboard");
    }
  }, [
    isOrganizationsLoading,
    organizationMissing,
    organizations.length,
    router,
  ]);

  async function handleLogout() {
    setIsLoggingOut(true);
    try {
      await logout();
      clear();
      router.replace("/");
    } catch {
      setIsLoggingOut(false);
    }
  }

  if (!isHydrated || isOrganizationsLoading || !organization) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <p className="text-muted-foreground text-sm">Loading organization...</p>
      </main>
    );
  }

  const navItems = [
    { href: organizationHomePath(slug), label: "Dashboard" },
    { href: organizationMembersPath(slug), label: "Members" },
    { href: organizationSettingsPath(slug), label: "Settings" },
    { href: organizationBillingPath(slug), label: "Billing" },
  ];

  return (
    <div className="bg-background flex min-h-screen flex-col md:flex-row">
      <aside className="border-border flex w-full flex-col gap-4 border-b p-4 md:w-64 md:border-r md:border-b-0">
        <div>
          <p className="text-muted-foreground text-xs tracking-wide uppercase">
            Organization
          </p>
          <OrganizationSwitcher />
        </div>

        <nav className="flex flex-row flex-wrap gap-2 md:flex-col">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  buttonVariants({ variant: active ? "default" : "ghost" }),
                  "justify-start",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-2 pt-4">
          <p className="text-muted-foreground truncate text-xs">
            {session?.user.email}
          </p>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={handleLogout}
            disabled={isLoggingOut}
          >
            {isLoggingOut ? "Signing out..." : "Logout"}
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-border flex items-center justify-between border-b px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">
              {organization.name}
            </h1>
            <p className="text-muted-foreground text-xs capitalize">
              {organization.role}
            </p>
          </div>
        </header>
        <div className="flex-1">{children}</div>
      </div>
    </div>
  );
}
