"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Button, buttonVariants } from "@/components/ui/button";
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
import { registerSchema, type RegisterFormValues } from "@/lib/auth/schemas";
import { cn } from "@/lib/utils";
import { fetchCurrentUser, registerWithEmail } from "@/services/auth";
import { useAuthStore } from "@/store/auth";

export function RegisterForm() {
  const router = useRouter();
  const setSession = useAuthStore((state) => state.setSession);
  const setUser = useAuthStore((state) => state.setUser);
  const [authError, setAuthError] = useState<string | null>(null);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  async function onSubmit(values: RegisterFormValues) {
    setAuthError(null);

    try {
      const result = await registerWithEmail(values);

      if (result.requiresEmailConfirmation || !result.session) {
        setRegisteredEmail(values.email);
        return;
      }

      setSession(result.session);
      const platformUser = await fetchCurrentUser();
      setUser(platformUser);
      router.replace("/dashboard");
    } catch (error) {
      setAuthError(
        error instanceof Error ? error.message : "Unable to create account",
      );
    }
  }

  if (registeredEmail) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Check your email</CardTitle>
          <CardDescription>
            We sent a verification link to confirm your account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm" role="status">
            A verification email was sent to{" "}
            <span className="font-medium">{registeredEmail}</span>.
          </p>
          <p className="text-muted-foreground text-sm">
            Open the link in that email to verify your address. You will be
            signed in automatically and redirected to your dashboard.
          </p>
          <p className="text-muted-foreground text-sm">
            If you do not see the email, check your spam folder.
          </p>
        </CardContent>
        <CardFooter className="flex flex-wrap gap-3">
          <Link
            href="/auth/login"
            className={cn(buttonVariants({ size: "lg" }))}
          >
            Go to sign in
          </Link>
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => setRegisteredEmail(null)}
          >
            Use a different email
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Create account</CardTitle>
        <CardDescription>Start using the SaaS Platform.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="space-y-2">
            <Label htmlFor="fullName">Full name</Label>
            <Input
              id="fullName"
              type="text"
              autoComplete="name"
              aria-invalid={Boolean(errors.fullName)}
              {...register("fullName")}
            />
            {errors.fullName ? (
              <p className="text-destructive text-sm">{errors.fullName.message}</p>
            ) : null}
          </div>

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
              autoComplete="new-password"
              aria-invalid={Boolean(errors.password)}
              {...register("password")}
            />
            {errors.password ? (
              <p className="text-destructive text-sm">{errors.password.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm password</Label>
            <Input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              aria-invalid={Boolean(errors.confirmPassword)}
              {...register("confirmPassword")}
            />
            {errors.confirmPassword ? (
              <p className="text-destructive text-sm">
                {errors.confirmPassword.message}
              </p>
            ) : null}
          </div>

          {authError ? (
            <p className="text-destructive text-sm" role="alert">
              {authError}
            </p>
          ) : null}

          <Button className="w-full" type="submit" disabled={isSubmitting} size="lg">
            {isSubmitting ? "Creating account..." : "Create account"}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="justify-center">
        <p className="text-muted-foreground text-sm">
          Already have an account?{" "}
          <Link className="text-foreground underline underline-offset-4" href="/auth/login">
            Sign in
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
