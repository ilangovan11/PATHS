import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";

const api = axios.create({
  baseURL,
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("paths_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Unauthorized anywhere -> drop the session; the AuthProvider reacts.
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("paths_token");
      localStorage.removeItem("paths_user");
      window.dispatchEvent(new CustomEvent("paths:unauthorized"));
    }
    return Promise.reject(error);
  }
);

export default api;