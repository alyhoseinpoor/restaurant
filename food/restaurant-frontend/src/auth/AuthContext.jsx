import { createContext, useContext, useState, useCallback } from 'react';
import { login as apiLogin, setTokens, clearTokens, getTokens, decodeToken } from '../api';

const AuthContext = createContext(null);

function currentUserFromStorage() {
  const { access } = getTokens();
  if (!access) return null;
  const payload = decodeToken(access);
  if (!payload) return null;
  return { id: payload.user_id, username: payload.username || null };
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(currentUserFromStorage);

  const login = useCallback(async (username, password) => {
    const data = await apiLogin(username, password);
    setTokens(data);
    const payload = decodeToken(data.access);
    setUser({ id: payload?.user_id, username });
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
