"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  resolveInitialOrganizationSlug,
  setLastSelectedOrganizationSlug,
} from "@/lib/organizations/active-organization";
import { organizationSectionPath } from "@/lib/organizations/paths";
import { listOrganizations } from "@/services/organizations";
import { useAuthStore } from "@/store/auth";

type LegacyOrganizationRedirectProps = {
  section: "dashboard" | "members" | "settings" | "billing";
};

export function LegacyOrganizationRedirect({
  section,
}: LegacyOrganizationRedirectProps) {
  const router = useRouter();
  const session = useAuthStore((state) => state.session);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    if (!session) {
      router.replace("/auth/login");
      return;
    }

    let isMounted = true;

    async function resolve() {
      try {
        const organizations = await listOrganizations();
        if (!isMounted) {
          return;
        }
        if (organizations.length === 0) {
          router.replace("/onboarding");
          return;
        }
        const slug = resolveInitialOrganizationSlug(organizations);
        if (!slug) {
          router.replace("/onboarding");
          return;
        }
        setLastSelectedOrganizationSlug(slug);
        router.replace(organizationSectionPath(slug, section));
      } catch (loadError) {
        if (isMounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load organizations",
          );
        }
      }
    }

    void resolve();
    return () => {
      isMounted = false;
    };
  }, [isHydrated, router, section, session]);

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <p className="text-muted-foreground text-sm" role={error ? "alert" : "status"}>
        {error ?? "Redirecting..."}
      </p>
    </main>
  );
}
