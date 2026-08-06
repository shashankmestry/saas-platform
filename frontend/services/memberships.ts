import axios from "axios";

import { apiClient } from "@/lib/api/client";
import type {
  ApiError,
  OrganizationInvitation,
  OrganizationMember,
} from "@/types";

function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<ApiError>(error)) {
    return error.response?.data?.detail ?? error.response?.data?.message ?? fallback;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

export async function listOrganizationMembers(
  organizationId: string,
): Promise<OrganizationMember[]> {
  try {
    const response = await apiClient.get<OrganizationMember[]>(
      `/api/v1/organizations/${organizationId}/members`,
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to load members"));
  }
}

export async function listOrganizationInvitations(
  organizationId: string,
): Promise<OrganizationInvitation[]> {
  try {
    const response = await apiClient.get<OrganizationInvitation[]>(
      `/api/v1/organizations/${organizationId}/invitations`,
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to load invitations"));
  }
}

export async function createOrganizationInvitation(
  organizationId: string,
  email: string,
): Promise<OrganizationInvitation> {
  try {
    const response = await apiClient.post<OrganizationInvitation>(
      `/api/v1/organizations/${organizationId}/invitations`,
      { email },
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to create invitation"));
  }
}

export async function revokeOrganizationInvitation(
  organizationId: string,
  invitationId: string,
): Promise<void> {
  try {
    await apiClient.delete(
      `/api/v1/organizations/${organizationId}/invitations/${invitationId}`,
    );
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to revoke invitation"));
  }
}

export async function acceptInvitation(
  token: string,
): Promise<OrganizationInvitation> {
  try {
    const response = await apiClient.post<OrganizationInvitation>(
      "/api/v1/invitations/accept",
      { token },
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to accept invitation"));
  }
}

export async function updateMemberRole(
  organizationId: string,
  membershipId: string,
  role: "owner" | "member",
): Promise<OrganizationMember> {
  try {
    const response = await apiClient.patch<OrganizationMember>(
      `/api/v1/organizations/${organizationId}/members/${membershipId}`,
      { role },
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to update member role"));
  }
}

export async function removeMember(
  organizationId: string,
  membershipId: string,
): Promise<void> {
  try {
    await apiClient.delete(
      `/api/v1/organizations/${organizationId}/members/${membershipId}`,
    );
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to remove member"));
  }
}

export async function leaveOrganization(organizationId: string): Promise<void> {
  try {
    await apiClient.post(`/api/v1/organizations/${organizationId}/leave`);
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to leave organization"));
  }
}

export async function transferOwnership(
  organizationId: string,
  membershipId: string,
): Promise<void> {
  try {
    await apiClient.post(
      `/api/v1/organizations/${organizationId}/ownership/transfer`,
      { membership_id: membershipId },
    );
  } catch (error) {
    throw new Error(getErrorMessage(error, "Unable to transfer ownership"));
  }
}
