import { z } from "zod";

const optionalTrimmed = z
  .string()
  .trim()
  .transform((value) => (value === "" ? null : value));

export const organizationProfileSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Organization name must be at least 2 characters")
    .max(255, "Organization name must be at most 255 characters"),
  slug: z.string(),
  website: optionalTrimmed
    .nullable()
    .refine(
      (value) =>
        value === null ||
        value.toLowerCase().startsWith("http://") ||
        value.toLowerCase().startsWith("https://"),
      "Website must start with http:// or https://",
    ),
  contact_email: optionalTrimmed
    .nullable()
    .refine(
      (value) => value === null || z.string().email().safeParse(value).success,
      "Enter a valid email address",
    ),
  phone: optionalTrimmed.nullable(),
  country_code: optionalTrimmed.nullable(),
  timezone: optionalTrimmed.nullable(),
  default_currency: optionalTrimmed.nullable(),
});

export type OrganizationProfileFormValues = z.infer<
  typeof organizationProfileSchema
>;
