"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useForm } from "react-hook-form";

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
import {
  setLastSelectedOrganizationSlug,
  resolveInitialOrganizationSlug,
} from "@/lib/organizations/active-organization";
import { organizationHomePath } from "@/lib/organizations/paths";
import {
  createOrganizationSchema,
  type CreateOrganizationFormValues,
} from "@/lib/organizations/schemas";
import { organizationKeys } from "@/lib/query-keys";
import { createOrganization, listOrganizations } from "@/services/organizations";
import { useAuthStore } from "@/store/auth";

function OnboardingFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const forceCreate = searchParams.get("new") === "1";
  const session = useAuthStore((state) => state.session);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isCheckingOrgs, setIsCheckingOrgs] = useState(!forceCreate);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateOrganizationFormValues>({
    resolver: zodResolver(createOrganizationSchema),
    defaultValues: {
      name: "",
    },
  });

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    if (!session) {
      router.replace("/auth/login");
      return;
    }

    if (forceCreate) {
      return;
    }

    let isMounted = true;

    async function checkOrganizations() {
      try {
        const organizations = await listOrganizations();
        if (!isMounted) {
          return;
        }

        if (organizations.length > 0) {
          const slug = resolveInitialOrganizationSlug(organizations);
          if (slug) {
            setLastSelectedOrganizationSlug(slug);
            router.replace(organizationHomePath(slug));
            return;
          }
        }

        setIsCheckingOrgs(false);
      } catch (error) {
        if (isMounted) {
          setAuthError(
            error instanceof Error
              ? error.message
              : "Unable to load organizations",
          );
          setIsCheckingOrgs(false);
        }
      }
    }

    void checkOrganizations();

    return () => {
      isMounted = false;
    };
  }, [forceCreate, isHydrated, router, session]);

  async function onSubmit(values: CreateOrganizationFormValues) {
    setAuthError(null);

    try {
      const organization = await createOrganization(values.name);
      setLastSelectedOrganizationSlug(organization.slug);
      await queryClient.invalidateQueries({ queryKey: organizationKeys.list() });
      router.replace(organizationHomePath(organization.slug));
    } catch (error) {
      setAuthError(
        error instanceof Error
          ? error.message
          : "Unable to create organization",
      );
    }
  }

  if (!isHydrated || isCheckingOrgs) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <p className="text-muted-foreground text-sm">Loading...</p>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create your organization</CardTitle>
          <CardDescription>
            Organizations are the top-level workspace for your team.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="space-y-2">
              <Label htmlFor="name">Organization name</Label>
              <Input id="name" autoComplete="organization" {...register("name")} />
              {errors.name ? (
                <p className="text-destructive text-sm">{errors.name.message}</p>
              ) : null}
            </div>

            {authError ? (
              <p className="text-destructive text-sm" role="alert">
                {authError}
              </p>
            ) : null}

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create organization"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}

export function OnboardingForm() {
  return (
    <Suspense
      fallback={
        <main className="flex flex-1 items-center justify-center px-6 py-16">
          <p className="text-muted-foreground text-sm">Loading...</p>
        </main>
      }
    >
      <OnboardingFormContent />
    </Suspense>
  );
}
