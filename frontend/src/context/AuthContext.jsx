import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { loginUser } from '../api/authApi';
import { decodeJwt } from '../utils/jwt';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('access_token') || '');
  const [userId, setUserId] = useState(localStorage.getItem('user_id') || '');

  useEffect(() => {
    if (token && !userId) {
      const payload = decodeJwt(token);
      const sub = payload?.sub || '';
      if (sub) {
        setUserId(sub);
        localStorage.setItem('user_id', sub);
      }
    }
  }, [token, userId]);

  const login = async (email, password) => {
    const response = await loginUser({ email, password });
    const accessToken = response?.access_token || '';
    const payload = decodeJwt(accessToken);
    const sub = payload?.sub || '';

    setToken(accessToken);
    setUserId(sub);
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('user_id', sub);

    return { token: accessToken, userId: sub };
  };

  const logout = () => {
    setToken('');
    setUserId('');
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
  };

  const value = useMemo(
    () => ({
      token,
      userId,
      isAuthenticated: Boolean(token),
      login,
      logout
    }),
    [token, userId]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
