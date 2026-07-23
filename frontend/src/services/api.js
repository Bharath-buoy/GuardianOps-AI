import axios from "axios";

// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js).
// In production, set VITE_API_BASE_URL to your deployed FastAPI backend.
const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";

const TOKEN_STORAGE_KEY = "guardianops_token";

export const api = axios.create({
  baseURL,
  timeout: 15000,
});

// Attach the JWT (if present) to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A 401 means the token is missing/expired — clear it and let AuthContext's
// consumers redirect to /login via ProtectedRoute on next render.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("[GuardianOps API Error]", error?.response?.data || error.message);
    if (error?.response?.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      window.dispatchEvent(new Event("guardianops:unauthorized"));
    }
    return Promise.reject(error);
  }
);

export const endpoints = {
  // --- Auth ---
  register: (payload) => api.post("/auth/register", payload),
  login: (payload) => api.post("/auth/login", payload),
  me: () => api.get("/auth/me"),
  registrationStatus: () => api.get("/auth/status"),

  // --- Existing platform endpoints ---
  dashboard: () => api.get("/dashboard"),
  infrastructure: (params) => api.get("/infrastructure", { params }),
  serviceDetail: (serviceId) => api.get(`/infrastructure/${serviceId}`),
  serviceLogs: (serviceId, params) => api.get(`/infrastructure/${serviceId}/logs`, { params }),
  incidents: (params) => api.get("/incidents", { params }),
  incidentDetail: (incidentId) => api.get(`/incidents/${incidentId}`),
  analytics: () => api.get("/analytics"),
  analyze: (serviceId) => api.post("/analyze", { service_id: serviceId }),
  workflowNodes: () => api.get("/workflow/nodes"),
  runWorkflow: (payload) => api.post("/workflow/run", payload || {}),
  workflowHistory: (params) => api.get("/workflow/history", { params }),
  health: () => api.get("/health"),

  // --- Real/live monitoring endpoints ---
  systemMetrics: () => api.get("/metrics"),
  systemMetricsHistory: (params) => api.get("/metrics/history", { params }),
  serviceMetricsHistory: (serviceId, params) => api.get(`/metrics/services/${serviceId}`, { params }),
  logs: (params) => api.get("/logs", { params }),
  recommendations: (params) => api.get("/recommendations", { params }),
};

export { TOKEN_STORAGE_KEY };
export default api;
