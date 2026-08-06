import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

import { API_URL } from "@/lib/constants";
import { getSafeReturnPath } from "@/lib/auth/return-path";
import { getSupabaseEnv } from "@/lib/supabase/env";

function buildPostAuthRedirect(origin: string, nextParam: string | null): URL {
  const safeNext = getSafeReturnPath(nextParam);

  if (safeNext) {
    return new URL(safeNext, origin);
  }

  const dashboardUrl = new URL("/dashboard", origin);
  dashboardUrl.searchParams.set("verified", "1");
  return dashboardUrl;
}

export async function GET(request: NextRequest) {
  const requestUrl = request.nextUrl;
  const code = requestUrl.searchParams.get("code");
  const error = requestUrl.searchParams.get("error");
  const errorDescription = requestUrl.searchParams.get("error_description");
  const nextParam = requestUrl.searchParams.get("next");
  const origin = requestUrl.origin;

  if (error) {
    const loginUrl = new URL("/auth/login", origin);
    loginUrl.searchParams.set(
      "error",
      errorDescription?.replace(/\+/g, " ") ||
        "Email verification failed. Please try again.",
    );
    const safeNext = getSafeReturnPath(nextParam);
    if (safeNext) {
      loginUrl.searchParams.set("next", safeNext);
    }
    return NextResponse.redirect(loginUrl);
  }

  if (!code) {
    const loginUrl = new URL("/auth/login", origin);
    loginUrl.searchParams.set(
      "error",
      "Missing verification code. Open the link from your email again.",
    );
    const safeNext = getSafeReturnPath(nextParam);
    if (safeNext) {
      loginUrl.searchParams.set("next", safeNext);
    }
    return NextResponse.redirect(loginUrl);
  }

  const destinationUrl = buildPostAuthRedirect(origin, nextParam);
  let redirectResponse = NextResponse.redirect(destinationUrl);
  const { supabaseUrl, supabasePublishableKey } = getSupabaseEnv();

  const supabase = createServerClient(supabaseUrl, supabasePublishableKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => {
          request.cookies.set(name, value);
        });

        redirectResponse = NextResponse.redirect(destinationUrl);

        cookiesToSet.forEach(({ name, value, options }) => {
          redirectResponse.cookies.set(name, value, options);
        });
      },
    },
  });

  const { data, error: exchangeError } =
    await supabase.auth.exchangeCodeForSession(code);

  if (exchangeError || !data.session) {
    const loginUrl = new URL("/auth/login", origin);
    loginUrl.searchParams.set(
      "error",
      exchangeError?.message ||
        "Unable to complete email verification. Please sign in.",
    );
    const safeNext = getSafeReturnPath(nextParam);
    if (safeNext) {
      loginUrl.searchParams.set("next", safeNext);
    }
    return NextResponse.redirect(loginUrl);
  }

  try {
    await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${data.session.access_token}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });
  } catch {
    // Destination page can retry JIT provisioning if this request fails.
  }

  return redirectResponse;
}
