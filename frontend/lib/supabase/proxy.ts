import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

import { getSupabaseEnv } from "@/lib/supabase/env";

function getSafeReturnPath(value: string | null): string | null {
  if (!value) {
    return null;
  }

  if (!value.startsWith("/") || value.startsWith("//")) {
    return null;
  }

  return value;
}

/**
 * Refresh the Supabase auth session and enforce authentication for protected routes.
 */
export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  });

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

        supabaseResponse = NextResponse.next({
          request,
        });

        cookiesToSet.forEach(({ name, value, options }) => {
          supabaseResponse.cookies.set(name, value, options);
        });
      },
    },
  });

  // Validate/refresh the JWT. Do not use getSession() for auth decisions.
  const { data } = await supabase.auth.getClaims();
  const isAuthenticated = Boolean(data?.claims);

  const pathname = request.nextUrl.pathname;
  const isDashboardRoute =
    pathname === "/dashboard" || pathname.startsWith("/dashboard/");
  const isOnboardingRoute =
    pathname === "/onboarding" || pathname.startsWith("/onboarding/");
  const isProtectedRoute = isDashboardRoute || isOnboardingRoute;
  const isAuthPage =
    pathname === "/auth/login" || pathname === "/auth/register";

  if (!isAuthenticated && isProtectedRoute) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/auth/login";
    loginUrl.search = "";
    const returnPath = `${pathname}${request.nextUrl.search}`;
    const safeReturn = getSafeReturnPath(returnPath);
    if (safeReturn) {
      loginUrl.searchParams.set("next", safeReturn);
    }
    return NextResponse.redirect(loginUrl);
  }

  if (isAuthenticated && isAuthPage) {
    const nextPath = getSafeReturnPath(request.nextUrl.searchParams.get("next"));
    const destination = request.nextUrl.clone();
    if (nextPath) {
      destination.pathname = nextPath.split("?")[0] || "/dashboard";
      const queryIndex = nextPath.indexOf("?");
      destination.search = queryIndex >= 0 ? nextPath.slice(queryIndex) : "";
    } else {
      destination.pathname = "/dashboard";
      destination.search = "";
    }
    return NextResponse.redirect(destination);
  }

  return supabaseResponse;
}
