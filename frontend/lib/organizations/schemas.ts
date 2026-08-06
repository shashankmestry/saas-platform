import { z } from "zod";

export const createOrganizationSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Organization name must be at least 2 characters")
    .max(255, "Organization name must be at most 255 characters"),
});

export type CreateOrganizationFormValues = z.infer<
  typeof createOrganizationSchema
>;
