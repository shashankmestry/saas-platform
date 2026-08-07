"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useOrganization } from "@/components/providers/organization-provider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function OrganizationSwitcher() {
  const router = useRouter();
  const { organizations, organization, switchOrganization } = useOrganization();
  const [open, setOpen] = useState(false);

  function handleSelect(slug: string) {
    setOpen(false);
    switchOrganization(slug);
  }

  function handleCreate() {
    setOpen(false);
    router.push("/onboarding?new=1");
  }

  return (
    <div className="relative">
      <Button
        type="button"
        variant="outline"
        className="w-full justify-between"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className="truncate">
          {organization?.name ?? "Select organization"}
        </span>
        <span className="text-muted-foreground text-xs">▾</span>
      </Button>

      {open ? (
        <>
          <button
            type="button"
            className="fixed inset-0 z-10 cursor-default"
            aria-label="Close organization menu"
            onClick={() => setOpen(false)}
          />
          <div className="bg-background absolute top-full right-0 left-0 z-20 mt-1 rounded-lg border border-border shadow-sm">
            <ul className="max-h-64 overflow-auto py-1" role="listbox">
              {organizations.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={item.id === organization?.id}
                    className={cn(
                      "hover:bg-muted w-full px-3 py-2 text-left text-sm",
                      item.id === organization?.id && "bg-muted font-medium",
                    )}
                    onClick={() => handleSelect(item.slug)}
                  >
                    <span className="block truncate">{item.name}</span>
                    <span className="text-muted-foreground text-xs">
                      {item.slug}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
            <div className="border-t border-border p-1">
              <button
                type="button"
                className="hover:bg-muted w-full rounded-md px-3 py-2 text-left text-sm"
                onClick={handleCreate}
              >
                + Create Organization
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
