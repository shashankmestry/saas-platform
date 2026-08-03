import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { APP_NAME } from "@/lib/constants";
import { cn } from "@/lib/utils";

export default function PublicHomePage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-24">
      <div className="flex w-full max-w-xl flex-col items-center gap-6 text-center">
        <div className="space-y-3">
          <h1 className="text-4xl font-semibold tracking-tight">{APP_NAME}</h1>
          <p className="text-muted-foreground text-lg">
            A production-ready foundation for building modern SaaS applications.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/auth/register"
            className={cn(buttonVariants({ size: "lg" }))}
          >
            Create Account
          </Link>
          <Link
            href="/auth/login"
            className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
          >
            Sign In
          </Link>
        </div>
      </div>
    </main>
  );
}
