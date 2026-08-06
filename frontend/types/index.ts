export type PlatformUser = {
  id: string;
  auth_user_id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Organization = {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
  role: string;
  permissions: string[];
};

export type {
  LogoUploadAuthorization,
  LogoUploadRequest,
  OrganizationProfile,
  OrganizationProfileUpdate,
} from "@/types/organization-profile";

export type OrganizationMember = {
  id: string;
  user_id: string;
  display_name: string | null;
  email: string;
  role: string;
  created_at: string;
};

export type OrganizationInvitation = {
  id: string;
  organization_id: string;
  email: string;
  role: string;
  expires_at: string;
  created_at: string;
  invite_url?: string | null;
};

export type ApiError = {
  detail?: string;
  message?: string;
};
