"use client";

import * as React from "react";
import { authService } from "@/lib/api";

interface Session {
  user?: { id: string; email: string; full_name?: string; locale?: string; is_superuser?: boolean };
  memberships?: Array<{ role: string; organization_id?: string; organization_name?: string; organization_code?: string }>;
  loaded: boolean;
}

interface AuthContextType {
  session: Session;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = React.useState<Session>({ loaded: false });

  const load = React.useCallback(async () => {
    try {
      const data = await authService.me();
      setSession({ user: data.user, memberships: data.memberships, loaded: true });
    } catch {
      setSession({ loaded: true });
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const login = async (email: string, password: string) => {
    await authService.login(email, password);
    await load();
  };

  const logout = async () => {
    try { await authService.logout(); } catch {}
    setSession({ loaded: true });
  };

  const refresh = async () => {
    try { await authService.refresh(); await load(); } catch { setSession({ loaded: true }); }
  };

  return (
    <AuthContext.Provider value={{ session, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useSession() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
