export function organizationHomePath(slug: string): string {
  return `/organizations/${slug}/dashboard`;
}

export function organizationMembersPath(slug: string): string {
  return `/organizations/${slug}/members`;
}

export function organizationSettingsPath(slug: string): string {
  return `/organizations/${slug}/settings`;
}

export function organizationBillingPath(slug: string): string {
  return `/organizations/${slug}/billing`;
}

export function organizationSectionPath(
  slug: string,
  section: "dashboard" | "members" | "settings" | "billing",
): string {
  return `/organizations/${slug}/${section}`;
}

/** Replace the slug segment in an organization-scoped pathname. */
export function replaceOrganizationSlugInPath(
  pathname: string,
  currentSlug: string,
  nextSlug: string,
): string {
  const prefix = `/organizations/${currentSlug}`;
  if (!pathname.startsWith(prefix)) {
    return organizationHomePath(nextSlug);
  }
  return `/organizations/${nextSlug}${pathname.slice(prefix.length)}` || organizationHomePath(nextSlug);
}
