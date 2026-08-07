"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { OrganizationLogoSection } from "@/components/common/organization-logo-section";
import { OrganizationPlanSection } from "@/components/common/organization-plan-section";
import { useOrganization } from "@/components/providers/organization-provider";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { OrganizationPermission } from "@/lib/auth/permissions";
import {
  COUNTRY_OPTIONS,
  CURRENCY_OPTIONS,
  TIMEZONE_OPTIONS,
} from "@/lib/organizations/locale-options";
import {
  organizationProfileSchema,
  type OrganizationProfileFormValues,
} from "@/lib/organizations/profile-schema";
import { organizationKeys } from "@/lib/query-keys";
import { cn } from "@/lib/utils";
import { updateOrganizationProfile } from "@/services/organizations";

const selectClassName = cn(
  "h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-base outline-none",
  "focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
  "disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50",
  "md:text-sm",
);

export function OrganizationSettingsContent() {
  const queryClient = useQueryClient();
  const { organization, profile, can, isLoading } = useOrganization();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const canView = can(OrganizationPermission.ORGANIZATION_VIEW);
  const canManage = can(OrganizationPermission.ORGANIZATION_MANAGE);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<OrganizationProfileFormValues>({
    resolver: zodResolver(organizationProfileSchema),
    defaultValues: {
      name: "",
      slug: "",
      website: "",
      contact_email: "",
      phone: "",
      country_code: "",
      timezone: "",
      default_currency: "",
    },
  });

  useEffect(() => {
    if (!profile) {
      return;
    }
    reset({
      name: profile.name,
      slug: profile.slug,
      website: profile.website ?? "",
      contact_email: profile.contact_email ?? "",
      phone: profile.phone ?? "",
      country_code: profile.country_code ?? "",
      timezone: profile.timezone ?? "",
      default_currency: profile.default_currency ?? "",
    });
  }, [profile, reset]);

  const saveMutation = useMutation({
    mutationFn: (values: OrganizationProfileFormValues) =>
      updateOrganizationProfile(organization!.id, {
        name: values.name,
        website: values.website,
        contact_email: values.contact_email,
        phone: values.phone,
        country_code: values.country_code,
        timezone: values.timezone,
        default_currency: values.default_currency,
      }),
    onSuccess: async (updated) => {
      setError(null);
      setSuccess("Organization settings saved.");
      reset({
        name: updated.name,
        slug: updated.slug,
        website: updated.website ?? "",
        contact_email: updated.contact_email ?? "",
        phone: updated.phone ?? "",
        country_code: updated.country_code ?? "",
        timezone: updated.timezone ?? "",
        default_currency: updated.default_currency ?? "",
      });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: organizationKeys.profile(organization!.id),
        }),
        queryClient.invalidateQueries({ queryKey: organizationKeys.list() }),
      ]);
    },
    onError: (saveError: Error) => {
      setSuccess(null);
      setError(saveError.message);
    },
  });

  function onSubmit(values: OrganizationProfileFormValues) {
    if (!canManage) {
      return;
    }
    setSuccess(null);
    setError(null);
    saveMutation.mutate(values);
  }

  if (isLoading) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <p className="text-muted-foreground text-sm">Loading settings...</p>
      </main>
    );
  }

  if (!organization || !canView) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle>Organization settings</CardTitle>
            <CardDescription>
              You do not have permission to view this organization&apos;s profile.
            </CardDescription>
          </CardHeader>
        </Card>
      </main>
    );
  }

  const readOnly = !canManage;

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <Card className="w-full max-w-xl">
        <CardHeader>
          <CardTitle>Organization settings</CardTitle>
          <CardDescription>
            {readOnly
              ? "View your organization profile. You need manage permission to edit."
              : "Update your organization profile and contact details."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            <OrganizationPlanSection
              organizationId={organization.id}
              enabled={canView}
            />
            <OrganizationLogoSection
              organizationId={organization.id}
              logoUrl={profile?.logo_url ?? null}
              canManage={canManage}
            />

            <div className="space-y-2">
              <Label htmlFor="name">Organization Name</Label>
              <Input
                id="name"
                disabled={readOnly || saveMutation.isPending}
                aria-invalid={Boolean(errors.name)}
                {...register("name")}
              />
              {errors.name ? (
                <p className="text-destructive text-sm">{errors.name.message}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="slug">Organization Slug</Label>
              <Input id="slug" readOnly disabled {...register("slug")} />
              <p className="text-muted-foreground text-xs">Slug cannot be changed.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="website">Website</Label>
              <Input
                id="website"
                type="url"
                placeholder="https://example.com"
                disabled={readOnly || saveMutation.isPending}
                aria-invalid={Boolean(errors.website)}
                {...register("website")}
              />
              {errors.website ? (
                <p className="text-destructive text-sm">{errors.website.message}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="contact_email">Contact Email</Label>
              <Input
                id="contact_email"
                type="email"
                disabled={readOnly || saveMutation.isPending}
                aria-invalid={Boolean(errors.contact_email)}
                {...register("contact_email")}
              />
              {errors.contact_email ? (
                <p className="text-destructive text-sm">
                  {errors.contact_email.message}
                </p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                type="tel"
                disabled={readOnly || saveMutation.isPending}
                aria-invalid={Boolean(errors.phone)}
                {...register("phone")}
              />
              {errors.phone ? (
                <p className="text-destructive text-sm">{errors.phone.message}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="country_code">Country</Label>
              <select
                id="country_code"
                className={selectClassName}
                disabled={readOnly || saveMutation.isPending}
                {...register("country_code")}
              >
                <option value="">Select country</option>
                {COUNTRY_OPTIONS.map((option) => (
                  <option key={option.code} value={option.code}>
                    {option.label} ({option.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="timezone">Timezone</Label>
              <select
                id="timezone"
                className={selectClassName}
                disabled={readOnly || saveMutation.isPending}
                {...register("timezone")}
              >
                <option value="">Select timezone</option>
                {TIMEZONE_OPTIONS.map((timezone) => (
                  <option key={timezone} value={timezone}>
                    {timezone}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="default_currency">Default Currency</Label>
              <select
                id="default_currency"
                className={selectClassName}
                disabled={readOnly || saveMutation.isPending}
                {...register("default_currency")}
              >
                <option value="">Select currency</option>
                {CURRENCY_OPTIONS.map((option) => (
                  <option key={option.code} value={option.code}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {error ? (
              <p className="text-destructive text-sm" role="alert">
                {error}
              </p>
            ) : null}
            {success ? (
              <p className="text-muted-foreground text-sm" role="status">
                {success}
              </p>
            ) : null}

            {canManage ? (
              <Button type="submit" disabled={saveMutation.isPending || !isDirty}>
                {saveMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
            ) : null}
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
