/**
 * Return a safe same-origin relative path for post-auth redirects.
 * Rejects protocol-relative and absolute URLs.
 */
export function getSafeReturnPath(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }

  if (!value.startsWith("/") || value.startsWith("//")) {
    return null;
  }

  return value;
}

export function buildLoginPath(returnPath?: string | null): string {
  const safe = getSafeReturnPath(returnPath);
  if (!safe) {
    return "/auth/login";
  }

  return `/auth/login?next=${encodeURIComponent(safe)}`;
}

export function buildRegisterPath(returnPath?: string | null): string {
  const safe = getSafeReturnPath(returnPath);
  if (!safe) {
    return "/auth/register";
  }

  return `/auth/register?next=${encodeURIComponent(safe)}`;
}
