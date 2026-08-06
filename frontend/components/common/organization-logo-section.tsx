"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  ALLOWED_LOGO_MIME_TYPES,
  MAX_LOGO_BYTES,
  isAllowedLogoMimeType,
} from "@/lib/organizations/logo";
import { organizationKeys } from "@/lib/query-keys";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";
import {
  confirmOrganizationLogoUpload,
  deleteOrganizationLogo,
  requestOrganizationLogoUpload,
} from "@/services/organizations";
import type { OrganizationProfile } from "@/types";

type OrganizationLogoSectionProps = {
  organizationId: string;
  logoUrl: string | null;
  canManage: boolean;
};

export function OrganizationLogoSection({
  organizationId,
  logoUrl,
  canManage,
}: OrganizationLogoSectionProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function invalidateProfile() {
    await queryClient.invalidateQueries({
      queryKey: organizationKeys.profile(organizationId),
    });
  }

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const authorization = await requestOrganizationLogoUpload(organizationId, {
        content_type: file.type,
        file_size: file.size,
      });

      const supabase = createSupabaseBrowserClient();
      const { error: uploadError } = await supabase.storage
        .from(authorization.bucket)
        .uploadToSignedUrl(authorization.path, authorization.token, file, {
          contentType: file.type,
          cacheControl: "3600",
        });

      if (uploadError) {
        throw new Error("Unable to upload logo to storage");
      }

      return confirmOrganizationLogoUpload(organizationId, authorization.path);
    },
    onSuccess: async (profile: OrganizationProfile) => {
      setError(null);
      setSuccess("Organization logo updated.");
      setPreviewUrl(null);
      queryClient.setQueryData(
        organizationKeys.profile(organizationId),
        profile,
      );
      await invalidateProfile();
    },
    onError: (uploadError: Error) => {
      setSuccess(null);
      setError(uploadError.message);
    },
  });

  const removeMutation = useMutation({
    mutationFn: () => deleteOrganizationLogo(organizationId),
    onSuccess: async (profile: OrganizationProfile) => {
      setError(null);
      setSuccess("Organization logo removed.");
      setPreviewUrl(null);
      queryClient.setQueryData(
        organizationKeys.profile(organizationId),
        profile,
      );
      await invalidateProfile();
    },
    onError: (removeError: Error) => {
      setSuccess(null);
      setError(removeError.message);
    },
  });

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }

    setError(null);
    setSuccess(null);

    if (!isAllowedLogoMimeType(file.type)) {
      setError("Logo must be a JPEG, PNG, or WebP image.");
      return;
    }

    if (file.size > MAX_LOGO_BYTES) {
      setError("Logo must be 2 MB or smaller.");
      return;
    }

    const localPreview = URL.createObjectURL(file);
    setPreviewUrl(localPreview);
    uploadMutation.mutate(file, {
      onSettled: () => {
        URL.revokeObjectURL(localPreview);
      },
    });
  }

  function handleRemove() {
    const confirmed = window.confirm("Remove the organization logo?");
    if (!confirmed) {
      return;
    }
    setError(null);
    setSuccess(null);
    removeMutation.mutate();
  }

  const displayUrl = previewUrl ?? logoUrl;
  const busy = uploadMutation.isPending || removeMutation.isPending;

  return (
    <div className="space-y-3 border-b border-border pb-4">
      <div className="space-y-1">
        <Label>Organization Logo</Label>
        <p className="text-muted-foreground text-xs">
          JPEG, PNG, or WebP. Maximum size 2 MB.
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="bg-muted flex h-20 w-20 items-center justify-center overflow-hidden rounded-lg border border-border">
          {displayUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={displayUrl}
              alt="Organization logo"
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-muted-foreground text-xs">No logo</span>
          )}
        </div>

        {canManage ? (
          <div className="flex flex-wrap gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept={ALLOWED_LOGO_MIME_TYPES.join(",")}
              className="hidden"
              onChange={handleFileChange}
            />
            <Button
              type="button"
              variant="outline"
              disabled={busy}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploadMutation.isPending ? "Uploading..." : "Change Logo"}
            </Button>
            {logoUrl ? (
              <Button
                type="button"
                variant="outline"
                disabled={busy}
                onClick={handleRemove}
              >
                {removeMutation.isPending ? "Removing..." : "Remove Logo"}
              </Button>
            ) : null}
          </div>
        ) : null}
      </div>

      {error ? (
        <p className="text-destructive text-sm" role="alert">
          {error}
        </p>
      ) : null}
      {success ? (
        <p className="text-muted-foreground text-sm" role="status">
          {success}
        </p>
      ) : null}
    </div>
  );
}
