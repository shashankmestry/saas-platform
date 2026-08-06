import type { Session } from "@supabase/supabase-js";
import axios from "axios";

import { apiClient } from "@/lib/api/client";
import { APP_URL, AUTH_CALLBACK_PATH } from "@/lib/constants";
import { getSafeReturnPath } from "@/lib/auth/return-path";
import type { LoginFormValues, RegisterFormValues } from "@/lib/auth/schemas";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { ApiError, PlatformUser } from "@/types";

function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<ApiError>(error)) {
    return error.response?.data?.detail ?? error.response?.data?.message ?? fallback;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

export function getAuthCallbackUrl(returnPath?: string | null): string {
  const base = `${APP_URL.replace(/\/$/, "")}${AUTH_CALLBACK_PATH}`;
  const safe = getSafeReturnPath(returnPath);

  if (!safe) {
    return base;
  }

  const url = new URL(base);
  url.searchParams.set("next", safe);
  return url.toString();
}

export async function registerWithEmail(
  values: RegisterFormValues,
  options?: { returnPath?: string | null },
): Promise<{ session: Session | null; requiresEmailConfirmation: boolean }> {
  const supabase = createSupabaseBrowserClient();
  const { data, error } = await supabase.auth.signUp({
    email: values.email,
    password: values.password,
    options: {
      // Preserve invitation/return path through email verification.
      emailRedirectTo: getAuthCallbackUrl(options?.returnPath),
      data: {
        full_name: values.fullName,
      },
    },
  });

  if (error) {
    throw new Error(error.message);
  }

  return {
    session: data.session,
    requiresEmailConfirmation: data.session === null,
  };
}

export async function loginWithEmail(values: LoginFormValues): Promise<Session> {
  const supabase = createSupabaseBrowserClient();
  const { data, error } = await supabase.auth.signInWithPassword({
    email: values.email,
    password: values.password,
  });

  if (error) {
    throw new Error(error.message);
  }

  if (!data.session) {
    throw new Error("Login succeeded but no session was returned");
  }

  return data.session;
}

export async function fetchCurrentUser(): Promise<PlatformUser> {
  try {
    const response = await apiClient.get<PlatformUser>("/api/v1/auth/me");
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to load platform user"));
  }
}

export async function logout(): Promise<void> {
  const supabase = createSupabaseBrowserClient();
  const { error } = await supabase.auth.signOut();

  if (error) {
    throw new Error(error.message);
  }
}
