"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, usePathname, useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";

import {
  can as hasPermission,
  type OrganizationPermission,
} from "@/lib/auth/permissions";
import { setLastSelectedOrganizationSlug } from "@/lib/organizations/active-organization";
import {
  organizationHomePath,
  replaceOrganizationSlugInPath,
} from "@/lib/organizations/paths";
import { membershipKeys, organizationKeys } from "@/lib/query-keys";
import {
  getOrganizationPlan,
  getOrganizationProfile,
  getOrganizationSubscription,
  listOrganizations,
} from "@/services/organizations";
import { useAuthStore } from "@/store/auth";
import type {
  Organization,
  OrganizationPlan,
  OrganizationProfile,
  OrganizationSubscription,
} from "@/types";

type OrganizationContextValue = {
  organizations: Organization[];
  organization: Organization | null;
  slug: string;
  role: string | null;
  permissions: string[];
  can: (permission: OrganizationPermission | string) => boolean;
  profile: OrganizationProfile | undefined;
  plan: OrganizationPlan | undefined;
  subscription: OrganizationSubscription | undefined;
  isLoading: boolean;
  isOrganizationsLoading: boolean;
  organizationMissing: boolean;
  switchOrganization: (nextSlug: string) => void;
  invalidateOrganizationQueries: () => Promise<void>;
};

const OrganizationContext = createContext<OrganizationContextValue | null>(null);

type OrganizationProviderProps = {
  children: ReactNode;
};

const EMPTY_ORGANIZATIONS: Organization[] = [];
const EMPTY_PERMISSIONS: string[] = [];

export function OrganizationProvider({ children }: OrganizationProviderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams<{ slug: string }>();
  const slug = typeof params.slug === "string" ? params.slug : "";
  const queryClient = useQueryClient();
  const session = useAuthStore((state) => state.session);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  const organizationsQuery = useQuery({
    queryKey: organizationKeys.list(),
    queryFn: listOrganizations,
    enabled: isHydrated && Boolean(session),
  });

  const organizations = organizationsQuery.data ?? EMPTY_ORGANIZATIONS;
  const organization =
    organizations.find((item) => item.slug === slug) ?? null;
  const organizationId = organization?.id ?? "";
  const organizationMissing =
    organizationsQuery.isSuccess && Boolean(slug) && organization === null;

  useEffect(() => {
    if (organization?.slug) {
      setLastSelectedOrganizationSlug(organization.slug);
    }
  }, [organization?.slug]);

  const profileQuery = useQuery({
    queryKey: organizationKeys.profile(organizationId),
    queryFn: () => getOrganizationProfile(organizationId),
    enabled: Boolean(organizationId),
  });

  const planQuery = useQuery({
    queryKey: organizationKeys.plan(organizationId),
    queryFn: () => getOrganizationPlan(organizationId),
    enabled: Boolean(organizationId),
  });

  const subscriptionQuery = useQuery({
    queryKey: organizationKeys.subscription(organizationId),
    queryFn: () => getOrganizationSubscription(organizationId),
    enabled: Boolean(organizationId),
  });

  const permissions = organization?.permissions ?? EMPTY_PERMISSIONS;

  const can = useCallback(
    (permission: OrganizationPermission | string) =>
      hasPermission(permissions, permission),
    [permissions],
  );

  const invalidateOrganizationQueries = useCallback(async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: organizationKeys.all }),
      queryClient.invalidateQueries({ queryKey: membershipKeys.all }),
      queryClient.invalidateQueries({ queryKey: ["profile"] }),
      queryClient.invalidateQueries({ queryKey: ["plan"] }),
      queryClient.invalidateQueries({ queryKey: ["subscription"] }),
      queryClient.invalidateQueries({ queryKey: ["members"] }),
      queryClient.invalidateQueries({ queryKey: ["invitations"] }),
    ]);
  }, [queryClient]);

  const switchOrganization = useCallback(
    (nextSlug: string) => {
      if (!nextSlug || nextSlug === slug) {
        return;
      }

      setLastSelectedOrganizationSlug(nextSlug);
      const destination = replaceOrganizationSlugInPath(pathname, slug, nextSlug);
      router.push(destination || organizationHomePath(nextSlug));

      void queryClient.invalidateQueries({
        predicate: (query) => {
          const key = query.queryKey;
          if (!Array.isArray(key) || key.length === 0) {
            return false;
          }
          const root = key[0];
          return (
            root === "profile" ||
            root === "plan" ||
            root === "subscription" ||
            root === "members" ||
            root === "invitations" ||
            root === "memberships" ||
            (root === "organizations" && key[1] !== "list")
          );
        },
      });
    },
    [pathname, queryClient, router, slug],
  );

  const value = useMemo<OrganizationContextValue>(
    () => ({
      organizations,
      organization,
      slug,
      role: organization?.role ?? null,
      permissions,
      can,
      profile: profileQuery.data,
      plan: planQuery.data,
      subscription: subscriptionQuery.data,
      isLoading:
        !isHydrated ||
        organizationsQuery.isLoading ||
        (Boolean(organizationId) &&
          (profileQuery.isLoading ||
            planQuery.isLoading ||
            subscriptionQuery.isLoading)),
      isOrganizationsLoading: !isHydrated || organizationsQuery.isLoading,
      organizationMissing,
      switchOrganization,
      invalidateOrganizationQueries,
    }),
    [
      organizations,
      organization,
      slug,
      permissions,
      can,
      profileQuery.data,
      profileQuery.isLoading,
      planQuery.data,
      planQuery.isLoading,
      subscriptionQuery.data,
      subscriptionQuery.isLoading,
      isHydrated,
      organizationsQuery.isLoading,
      organizationId,
      organizationMissing,
      switchOrganization,
      invalidateOrganizationQueries,
    ],
  );

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization(): OrganizationContextValue {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error("useOrganization must be used within OrganizationProvider");
  }
  return context;
}
