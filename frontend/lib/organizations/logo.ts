export const ALLOWED_LOGO_MIME_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
] as const;

export type AllowedLogoMimeType = (typeof ALLOWED_LOGO_MIME_TYPES)[number];

export const MAX_LOGO_BYTES = 2 * 1024 * 1024;

export function isAllowedLogoMimeType(value: string): value is AllowedLogoMimeType {
  return (ALLOWED_LOGO_MIME_TYPES as readonly string[]).includes(value);
}
