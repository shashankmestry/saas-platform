"use client";

import { useEffect, type ReactNode } from "react";

import { fetchCurrentUser } from "@/services/auth";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/store/auth";

type AuthProviderProps = {
  children: ReactNode;
};

/**
 * Mirrors the Supabase cookie session into UI state and loads the platform user.
 * Supabase remains the source of truth for authentication persistence.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const setSession = useAuthStore((state) => state.setSession);
  const setUser = useAuthStore((state) => state.setUser);
  const setHydrated = useAuthStore((state) => state.setHydrated);
  const clear = useAuthStore((state) => state.clear);

  useEffect(() => {
    const supabase = createSupabaseBrowserClient();
    let isMounted = true;

    async function syncPlatformUser(hasSession: boolean) {
      if (!hasSession) {
        if (isMounted) {
          setUser(null);
        }
        return;
      }

      try {
        const platformUser = await fetchCurrentUser();
        if (isMounted) {
          setUser(platformUser);
        }
      } catch {
        if (isMounted) {
          setUser(null);
        }
      }
    }

    async function hydrate() {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!isMounted) {
        return;
      }

      setSession(session);
      await syncPlatformUser(Boolean(session));

      if (isMounted) {
        setHydrated(true);
      }
    }

    void hydrate();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      setSession(session);

      if (!session) {
        clear();
        setHydrated(true);
        return;
      }

      if (event === "SIGNED_IN" || event === "INITIAL_SESSION") {
        void syncPlatformUser(true);
      }

      setHydrated(true);
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, [clear, setHydrated, setSession, setUser]);

  return children;
}
