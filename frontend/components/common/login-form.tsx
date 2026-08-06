"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginSchema, type LoginFormValues } from "@/lib/auth/schemas";
import {
  buildRegisterPath,
  getSafeReturnPath,
} from "@/lib/auth/return-path";
import { fetchCurrentUser, loginWithEmail } from "@/services/auth";
import { useAuthStore } from "@/store/auth";

function LoginFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setSession = useAuthStore((state) => state.setSession);
  const setUser = useAuthStore((state) => state.setUser);
  const [authError, setAuthError] = useState<string | null>(null);
  const nextPath = getSafeReturnPath(searchParams.get("next"));

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  useEffect(() => {
    const error = searchParams.get("error");
    if (error) {
      setAuthError(error);
    }
  }, [searchParams]);

  async function onSubmit(values: LoginFormValues) {
    setAuthError(null);

    try {
      const session = await loginWithEmail(values);
      setSession(session);

      const platformUser = await fetchCurrentUser();
      setUser(platformUser);

      router.replace(nextPath ?? "/dashboard");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to sign in";
      const normalized = message.toLowerCase();

      if (
        normalized.includes("email not confirmed") ||
        normalized.includes("confirm")
      ) {
        setAuthError(
          "Your email is not verified yet. Open the verification link we sent you, then try signing in again.",
        );
        return;
      }

      setAuthError(message);
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Sign in</CardTitle>
        <CardDescription>Access your SaaS Platform account.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              aria-invalid={Boolean(errors.email)}
              {...register("email")}
            />
            {errors.email ? (
              <p className="text-destructive text-sm">{errors.email.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              aria-invalid={Boolean(errors.password)}
              {...register("password")}
            />
            {errors.password ? (
              <p className="text-destructive text-sm">{errors.password.message}</p>
            ) : null}
          </div>

          {authError ? (
            <p className="text-destructive text-sm" role="alert">
              {authError}
            </p>
          ) : null}

          <Button className="w-full" type="submit" disabled={isSubmitting} size="lg">
            {isSubmitting ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="justify-center">
        <p className="text-muted-foreground text-sm">
          Need an account?{" "}
          <Link
            className="text-foreground underline underline-offset-4"
            href={buildRegisterPath(nextPath)}
          >
            Create account
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}

export function LoginForm() {
  return (
    <Suspense fallback={<Card className="w-full max-w-md" />}>
      <LoginFormContent />
    </Suspense>
  );
}
