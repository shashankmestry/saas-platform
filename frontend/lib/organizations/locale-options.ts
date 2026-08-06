/** Lightweight ISO 3166-1 alpha-2 options for organization settings. */
export const COUNTRY_OPTIONS = [
  { code: "AU", label: "Australia" },
  { code: "BR", label: "Brazil" },
  { code: "CA", label: "Canada" },
  { code: "DE", label: "Germany" },
  { code: "FR", label: "France" },
  { code: "GB", label: "United Kingdom" },
  { code: "IN", label: "India" },
  { code: "JP", label: "Japan" },
  { code: "SG", label: "Singapore" },
  { code: "US", label: "United States" },
] as const;

/** Common IANA timezone identifiers. */
export const TIMEZONE_OPTIONS = [
  "Africa/Johannesburg",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/New_York",
  "America/Sao_Paulo",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Asia/Singapore",
  "Asia/Tokyo",
  "Australia/Sydney",
  "Europe/Berlin",
  "Europe/London",
  "Europe/Paris",
  "UTC",
] as const;

/** Common ISO 4217 currency codes. */
export const CURRENCY_OPTIONS = [
  { code: "AUD", label: "AUD — Australian Dollar" },
  { code: "BRL", label: "BRL — Brazilian Real" },
  { code: "CAD", label: "CAD — Canadian Dollar" },
  { code: "EUR", label: "EUR — Euro" },
  { code: "GBP", label: "GBP — British Pound" },
  { code: "INR", label: "INR — Indian Rupee" },
  { code: "JPY", label: "JPY — Japanese Yen" },
  { code: "SGD", label: "SGD — Singapore Dollar" },
  { code: "USD", label: "USD — US Dollar" },
] as const;
