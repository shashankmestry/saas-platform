import { NextResponse, type NextRequest } from "next/server";

/**
 * Frontend proxy foundation.
 * Authentication and route protection will be added in a later step.
 */
export function proxy(_request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
