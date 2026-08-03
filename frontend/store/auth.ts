import type { Session } from "@supabase/supabase-js";
import { create } from "zustand";

import type { PlatformUser } from "@/types";

type AuthState = {
  session: Session | null;
  user: PlatformUser | null;
  isHydrated: boolean;
  setSession: (session: Session | null) => void;
  setUser: (user: PlatformUser | null) => void;
  setHydrated: (isHydrated: boolean) => void;
  clear: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  session: null,
  user: null,
  isHydrated: false,
  setSession: (session) => set({ session }),
  setUser: (user) => set({ user }),
  setHydrated: (isHydrated) => set({ isHydrated }),
  clear: () => set({ session: null, user: null }),
}));
