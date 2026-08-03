import axios from "axios";

import { API_URL } from "@/lib/constants";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use(async (config) => {
  const supabase = createSupabaseBrowserClient();

  // Read the current Supabase session (cookie-backed). Do not cache tokens separately.
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }

  return config;
});
