import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authApi, onUnauthorized, refreshCsrf, setCsrfToken } from './api.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const body = await authApi.me();
      setUser(body?.data || null);
      await refreshCsrf();
      return body?.data || null;
    } catch {
      setUser(null);
      setCsrfToken(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    onUnauthorized(() => setUser(null));
    load();
  }, [load]);

  const login = useCallback(
    async ({ email, role = 'participant', fullName }) => {
      await authApi.login({ email, role, full_name: fullName });
      return load();
    },
    [load],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setCsrfToken(null);
      setUser(null);
    }
  }, []);

  const value = useMemo(() => {
    const roles = user?.roles?.map((grant) => grant.role) || [];
    const isStaff = roles.some((role) => role !== 'participant');
    return {
      user,
      loading,
      login,
      logout,
      reload: load,
      roles,
      isStaff,
      isSuperAdmin: roles.includes('super_admin'),
    };
  }, [user, loading, login, logout, load]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
