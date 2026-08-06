"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
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
  createOrganizationSchema,
  type CreateOrganizationFormValues,
} from "@/lib/organizations/schemas";
import { createOrganization, listOrganizations } from "@/services/organizations";
import { useAuthStore } from "@/store/auth";

export function OnboardingForm() {
  const router = useRouter();
  const session = useAuthStore((state) => state.session);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isCheckingOrgs, setIsCheckingOrgs] = useState(true);

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

    let isMounted = true;

    async function checkOrganizations() {
      try {
        const organizations = await listOrganizations();
        if (!isMounted) {
          return;
        }

        if (organizations.length > 0) {
          router.replace("/dashboard");
          return;
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
  }, [isHydrated, router, session]);

  async function onSubmit(values: CreateOrganizationFormValues) {
    setAuthError(null);

    try {
      await createOrganization(values.name);
      router.replace("/dashboard");
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
            Set up your workspace to continue using the platform.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="space-y-2">
              <Label htmlFor="name">Organization Name</Label>
              <Input
                id="name"
                autoComplete="organization"
                placeholder="Acme Technologies"
                {...register("name")}
              />
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
              {isSubmitting ? "Creating..." : "Create Organization"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
