"use client";

import { useCallback, useMemo } from "react";

import {
  can as hasPermission,
  type OrganizationPermission,
} from "@/lib/auth/permissions";
import type { Organization } from "@/types";

export function useOrganizationPermissions(
  organization: Organization | null | undefined,
) {
  const permissions = organization?.permissions ?? [];

  const can = useCallback(
    (permission: OrganizationPermission | string) =>
      hasPermission(permissions, permission),
    [permissions],
  );

  return useMemo(
    () => ({
      role: organization?.role ?? null,
      permissions,
      can,
    }),
    [can, organization?.role, permissions],
  );
}
