/**
 * useAuth - manages authentication state with localStorage persistence.
 */
import { useCallback, useEffect, useState } from "react";
import api from "../services/api";

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const restore = async () => {
      const token = api.getStoredToken();
      if (!token) {
        if (!cancelled) {
          setLoading(false);
        }
        return;
      }

      api.setToken(token);

      try {
        const me = await api.getMe();
        if (!cancelled) {
          setUser(me);
        }
      } catch {
        api.logout();
        if (!cancelled) {
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    restore();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    setError("");
    try {
      const data = await api.login(email, password);
      setUser(data.user);
      return data;
    } catch (err) {
      setError(err.message || "Login failed.");
      throw err;
    }
  }, []);

  const register = useCallback(async (username, email, password, fullName) => {
    setError("");
    try {
      const data = await api.register(username, email, password, fullName);
      setUser(data.user);
      return data;
    } catch (err) {
      setError(err.message || "Registration failed.");
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    api.logout();
    setUser(null);
  }, []);

  return { user, loading, error, login, register, logout };
}
