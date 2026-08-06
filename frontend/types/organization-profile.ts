export type OrganizationProfile = {
  id: string;
  name: string;
  slug: string;
  website: string | null;
  contact_email: string | null;
  phone: string | null;
  country_code: string | null;
  timezone: string | null;
  default_currency: string | null;
  logo_url: string | null;
};

export type OrganizationProfileUpdate = {
  name?: string;
  website?: string | null;
  contact_email?: string | null;
  phone?: string | null;
  country_code?: string | null;
  timezone?: string | null;
  default_currency?: string | null;
};

export type LogoUploadAuthorization = {
  bucket: string;
  path: string;
  token: string;
  signed_url: string;
};

export type LogoUploadRequest = {
  content_type: string;
  file_size: number;
};
