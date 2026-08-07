const STORAGE_KEY = "saas-platform.active-organization-slug";

export function getLastSelectedOrganizationSlug(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value && value.trim() ? value.trim() : null;
  } catch {
    return null;
  }
}

export function setLastSelectedOrganizationSlug(slug: string): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(STORAGE_KEY, slug);
  } catch {
    // Ignore quota / private-mode failures; preference is best-effort.
  }
}

export function clearLastSelectedOrganizationSlug(): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore storage failures.
  }
}

/**
 * Pick which organization to open after login / when resolving /dashboard.
 *
 * Pass `storedSlug` to override localStorage (tests / non-browser callers).
 * Omit it to read the UI preference from browser localStorage.
 */
export function resolveInitialOrganizationSlug(
  organizations: readonly { slug: string }[],
  storedSlug?: string | null,
): string | null {
  if (organizations.length === 0) {
    return null;
  }

  if (organizations.length === 1) {
    return organizations[0].slug;
  }

  const stored =
    storedSlug === undefined ? getLastSelectedOrganizationSlug() : storedSlug;
  if (stored && organizations.some((organization) => organization.slug === stored)) {
    return stored;
  }

  return organizations[0].slug;
}
