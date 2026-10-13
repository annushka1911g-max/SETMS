// =============================================================================
// SETMS — Typed API Client
// Centralized axios instance with auth header injection and error normalization.
// =============================================================================
import axios, { AxiosError, type AxiosResponse } from 'axios';
import type {
  Ambulance,
  Corridor,
  DashboardSummary,
  Emergency,
  Hospital,
  Paginated,
  TokenResponse,
  TrafficSignal,
  User,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api/v1`
  : '/api/v1';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// ---- Auth token injection ----
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('setms_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---- Global error handling / session expiry ----
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear stale token and redirect to login
      localStorage.removeItem('setms_token');
      localStorage.removeItem('setms_user');
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login?session=expired';
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string })?.detail;
    if (detail) return detail;
    if (error.response?.status === 503) return 'Service temporarily unavailable. Please retry.';
    if (error.response?.status === 429) return 'Too many requests. Please wait a moment.';
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred.';
}

// =============================================================================
// Auth API
// =============================================================================
export const authApi = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>('/auth/login', { email, password });
    return res.data;
  },
  register: async (email: string, fullName: string, password: string, role: string): Promise<User> => {
    const res = await apiClient.post<User>('/auth/register', {
      email, full_name: fullName, password, role,
    });
    return res.data;
  },
  me: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },
};

// =============================================================================
// Dashboard API
// =============================================================================
export const dashboardApi = {
  summary: async (): Promise<DashboardSummary> => {
    const res = await apiClient.get<DashboardSummary>('/dashboard/summary');
    return res.data;
  },
  activity: async (limit = 20) => {
    const res = await apiClient.get('/dashboard/activity', { params: { limit } });
    return res.data;
  },
};

// =============================================================================
// Ambulance API
// =============================================================================
export const ambulanceApi = {
  list: async (params?: { status?: string; skip?: number; limit?: number }): Promise<Paginated<Ambulance>> => {
    const res = await apiClient.get<Paginated<Ambulance>>('/ambulances', { params });
    return res.data;
  },
  get: async (id: string): Promise<Ambulance> => {
    const res = await apiClient.get<Ambulance>(`/ambulances/${id}`);
    return res.data;
  },
  create: async (data: { registration_number: string; call_sign: string; vehicle_type?: string }): Promise<Ambulance> => {
    const res = await apiClient.post<Ambulance>('/ambulances', data);
    return res.data;
  },
  update: async (id: string, data: Partial<Ambulance>): Promise<Ambulance> => {
    const res = await apiClient.patch<Ambulance>(`/ambulances/${id}`, data);
    return res.data;
  },
  updateLocation: async (id: string, lat: number, lng: number, speedKmh?: number, source = 'SIMULATED') => {
    const res = await apiClient.post(`/ambulances/${id}/location`, {
      latitude: lat, longitude: lng, speed_kmh: speedKmh, source,
    });
    return res.data;
  },
};

// =============================================================================
// Emergency API
// =============================================================================
export const emergencyApi = {
  list: async (params?: { status?: string; severity?: string; skip?: number; limit?: number }): Promise<Paginated<Emergency>> => {
    const res = await apiClient.get<Paginated<Emergency>>('/emergencies', { params });
    return res.data;
  },
  get: async (id: string): Promise<Emergency> => {
    const res = await apiClient.get<Emergency>(`/emergencies/${id}`);
    return res.data;
  },
  create: async (data: {
    ambulance_id: string;
    destination_hospital_id?: string;
    severity?: string;
    description?: string;
    origin_lat?: number;
    origin_lng?: number;
  }): Promise<Emergency> => {
    const res = await apiClient.post<Emergency>('/emergencies', data);
    return res.data;
  },
  activate: async (id: string): Promise<Emergency> => {
    const res = await apiClient.post<Emergency>(`/emergencies/${id}/activate`);
    return res.data;
  },
  complete: async (id: string): Promise<Emergency> => {
    const res = await apiClient.post<Emergency>(`/emergencies/${id}/complete`);
    return res.data;
  },
  cancel: async (id: string): Promise<Emergency> => {
    const res = await apiClient.post<Emergency>(`/emergencies/${id}/cancel`);
    return res.data;
  },
};

// =============================================================================
// Signal API
// =============================================================================
export const signalApi = {
  list: async (): Promise<Paginated<TrafficSignal>> => {
    const res = await apiClient.get<Paginated<TrafficSignal>>('/signals');
    return res.data;
  },
  get: async (id: string): Promise<TrafficSignal> => {
    const res = await apiClient.get<TrafficSignal>(`/signals/${id}`);
    return res.data;
  },
  setMode: async (id: string, mode: string, reason?: string): Promise<TrafficSignal> => {
    const res = await apiClient.post<TrafficSignal>(`/signals/${id}/mode`, { mode, reason });
    return res.data;
  },
  events: async (id: string, limit = 50) => {
    const res = await apiClient.get(`/signals/${id}/events`, { params: { limit } });
    return res.data;
  },
};

// =============================================================================
// Corridor API
// =============================================================================
export const corridorApi = {
  list: async (params?: { status?: string }): Promise<Paginated<Corridor>> => {
    const res = await apiClient.get<Paginated<Corridor>>('/corridors', { params });
    return res.data;
  },
  get: async (id: string): Promise<Corridor> => {
    const res = await apiClient.get<Corridor>(`/corridors/${id}`);
    return res.data;
  },
  plan: async (emergency_id: string, signal_ids?: string[]): Promise<Corridor> => {
    const res = await apiClient.post<Corridor>('/corridors/plan', { emergency_id, signal_ids: signal_ids ?? [] });
    return res.data;
  },
  approve: async (id: string): Promise<Corridor> => {
    const res = await apiClient.post<Corridor>(`/corridors/${id}/approve`);
    return res.data;
  },
  cancel: async (id: string): Promise<Corridor> => {
    const res = await apiClient.post<Corridor>(`/corridors/${id}/cancel`);
    return res.data;
  },
};

// =============================================================================
// Hospital API
// =============================================================================
export const hospitalApi = {
  list: async (): Promise<Paginated<Hospital>> => {
    const res = await apiClient.get<Paginated<Hospital>>('/hospitals');
    return res.data;
  },
  incoming: async () => {
    const res = await apiClient.get('/hospitals/incoming');
    return res.data;
  },
  updateReadiness: async (id: string, data: { is_ready: boolean; emergency_bays_available?: number; readiness_note?: string }): Promise<Hospital> => {
    const res = await apiClient.patch<Hospital>(`/hospitals/${id}/readiness`, data);
    return res.data;
  },
};

// =============================================================================
// Analytics API
// =============================================================================
export const analyticsApi = {
  summary: async () => {
    const res = await apiClient.get('/analytics/summary');
    return res.data;
  },
  emergencies: async (days = 30) => {
    const res = await apiClient.get('/analytics/emergencies', { params: { days } });
    return res.data;
  },
  performance: async () => {
    const res = await apiClient.get('/analytics/performance');
    return res.data;
  },
};
