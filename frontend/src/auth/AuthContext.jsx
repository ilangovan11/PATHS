import { useEffect, useState } from "react";
import api from "../api/client";
import { AuthContext } from "./context";

const USER_KEY = "paths_user";
const TOKEN_KEY = "paths_token";

function readUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(readUser);

  useEffect(() => {
    const onUnauthorized = () => {
      setToken(null);
      setUser(null);
    };
    window.addEventListener("paths:unauthorized", onUnauthorized);
    return () => window.removeEventListener("paths:unauthorized", onUnauthorized);
  }, []);

  const login = async (email, password) => {
    const res = await api.post("/login", { email, password });
    const { access_token, role } = res.data;
    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(USER_KEY, JSON.stringify({ email, role }));
    setToken(access_token);
    setUser({ email, role });
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAdmin: user?.role === "admin",
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}