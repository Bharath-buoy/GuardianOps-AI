import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { endpoints, TOKEN_STORAGE_KEY } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const clearSession = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  // Whenever a request gets a 401, api.js dispatches this event so every
  // consumer of AuthContext (i.e. ProtectedRoute) immediately re-renders
  // into the logged-out state instead of waiting on a stale token.
  useEffect(() => {
    const handler = () => clearSession();
    window.addEventListener("guardianops:unauthorized", handler);
    return () => window.removeEventListener("guardianops:unauthorized", handler);
  }, [clearSession]);

  // On first load, if a token exists, validate it against /auth/me so a
  // stale/expired token doesn't silently render protected pages.
  useEffect(() => {
    let mounted = true;
    async function bootstrap() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await endpoints.me();
        if (mounted) setUser(res.data);
      } catch {
        if (mounted) clearSession();
      } finally {
        if (mounted) setLoading(false);
      }
    }
    bootstrap();
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await endpoints.login({ email, password });
    localStorage.setItem(TOKEN_STORAGE_KEY, res.data.access_token);
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data.user;
  }, []);

  const register = useCallback(async (name, email, password) => {
    const res = await endpoints.register({ name, email, password });
    localStorage.setItem(TOKEN_STORAGE_KEY, res.data.access_token);
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data.user;
  }, []);

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      isAuthenticated: Boolean(token && user),
      login,
      register,
      logout,
    }),
    [token, user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
