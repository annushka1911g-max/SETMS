// =============================================================================
// SETMS — Auth Context
// =============================================================================
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { authApi } from '../api/client';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('setms_token'),
    isLoading: true,
    isAuthenticated: false,
  });

  // Validate stored token on mount
  useEffect(() => {
    const token = localStorage.getItem('setms_token');
    if (!token) {
      setState(s => ({ ...s, isLoading: false }));
      return;
    }
    authApi.me()
      .then(user => setState({ user, token, isLoading: false, isAuthenticated: true }))
      .catch(() => {
        localStorage.removeItem('setms_token');
        localStorage.removeItem('setms_user');
        setState({ user: null, token: null, isLoading: false, isAuthenticated: false });
      });
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokenData = await authApi.login(email, password);
    localStorage.setItem('setms_token', tokenData.access_token);
    const user = await authApi.me();
    localStorage.setItem('setms_user', JSON.stringify(user));
    setState({ user, token: tokenData.access_token, isLoading: false, isAuthenticated: true });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('setms_token');
    localStorage.removeItem('setms_user');
    setState({ user: null, token: null, isLoading: false, isAuthenticated: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
