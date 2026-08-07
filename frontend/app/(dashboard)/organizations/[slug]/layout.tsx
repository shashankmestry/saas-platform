"use client";

import { OrganizationProvider } from "@/components/providers/organization-provider";
import { OrganizationShell } from "@/components/common/organization-shell";

export default function OrganizationLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <OrganizationProvider>
      <OrganizationShell>{children}</OrganizationShell>
    </OrganizationProvider>
  );
}
