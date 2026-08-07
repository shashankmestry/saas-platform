import axios from "axios";

import { apiClient } from "@/lib/api/client";
import type {
  LogoUploadAuthorization,
  LogoUploadRequest,
  Organization,
  OrganizationPlan,
  OrganizationProfile,
  OrganizationProfileUpdate,
  OrganizationSubscription,
} from "@/types";

function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { detail?: unknown; message?: string }
      | undefined;
    const detail = data?.detail;
    if (typeof detail === "string" && detail) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string } | string;
      if (typeof first === "object" && first && "msg" in first && first.msg) {
        return first.msg;
      }
      return String(first);
    }
    if (typeof data?.message === "string" && data.message) {
      return data.message;
    }
    return fallback;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

export async function listOrganizations(): Promise<Organization[]> {
  try {
    const response = await apiClient.get<Organization[]>("/api/v1/organizations");
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to load organizations"));
  }
}

export async function createOrganization(name: string): Promise<Organization> {
  try {
    const response = await apiClient.post<Organization>("/api/v1/organizations", {
      name,
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to create organization"));
  }
}

export async function getOrganizationProfile(
  organizationId: string,
): Promise<OrganizationProfile> {
  try {
    const response = await apiClient.get<OrganizationProfile>(
      `/api/v1/organizations/${organizationId}/profile`,
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to load organization profile"));
  }
}

export async function updateOrganizationProfile(
  organizationId: string,
  payload: OrganizationProfileUpdate,
): Promise<OrganizationProfile> {
  try {
    const response = await apiClient.patch<OrganizationProfile>(
      `/api/v1/organizations/${organizationId}/profile`,
      payload,
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to update organization profile"));
  }
}

export async function requestOrganizationLogoUpload(
  organizationId: string,
  payload: LogoUploadRequest,
): Promise<LogoUploadAuthorization> {
  try {
    const response = await apiClient.post<LogoUploadAuthorization>(
      `/api/v1/organizations/${organizationId}/logo/upload`,
      payload,
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to authorize logo upload"));
  }
}

export async function confirmOrganizationLogoUpload(
  organizationId: string,
  path: string,
): Promise<OrganizationProfile> {
  try {
    const response = await apiClient.post<OrganizationProfile>(
      `/api/v1/organizations/${organizationId}/logo/confirm`,
      { path },
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to confirm logo upload"));
  }
}

export async function deleteOrganizationLogo(
  organizationId: string,
): Promise<OrganizationProfile> {
  try {
    const response = await apiClient.delete<OrganizationProfile>(
      `/api/v1/organizations/${organizationId}/logo`,
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to remove organization logo"));
  }
}

export async function getOrganizationPlan(
  organizationId: string,
): Promise<OrganizationPlan> {
  try {
    const response = await apiClient.get<OrganizationPlan>(
      `/api/v1/organizations/${organizationId}/plan`,
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to load organization plan"));
  }
}

export async function getOrganizationSubscription(
  organizationId: string,
): Promise<OrganizationSubscription> {
  try {
    const response = await apiClient.get<OrganizationSubscription>(
      `/api/v1/organizations/${organizationId}/subscription`,
    );
    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(error, "Unable to load organization subscription"),
    );
  }
}
