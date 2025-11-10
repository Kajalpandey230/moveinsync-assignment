/**
 * API Service for Alert Management System
 */

import axios, { AxiosInstance } from 'axios';
import type {
  AlertSummary,
  TopOffender,
  RecentActivity,
  TrendDataPoint,
  Alert,
} from '../types';

const api: AxiosInstance = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests
api.interceptors.request.use((config: any) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors (but not on login endpoint)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Don't redirect if we're already on login page or if it's a login request
      const isLoginRequest = error.config?.url?.includes('/auth/login');
      if (!isLoginRequest && window.location.pathname !== '/login') {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// API functions
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me')
};

export const dashboardAPI = {
  getSummary: () => api.get<AlertSummary>('/api/dashboard/summary'),
  getTopOffenders: (limit = 5) => api.get<TopOffender[]>(`/api/dashboard/top-offenders?limit=${limit}`),
  getRecentActivities: (limit = 20) => api.get<RecentActivity[]>(`/api/dashboard/recent-activities?limit=${limit}`),
  getAutoClosedAlerts: (hours = 24) => api.get<Alert[]>(`/api/dashboard/auto-closed?hours=${hours}`),
  getTrends: (days = 7) => api.get<TrendDataPoint[]>(`/api/dashboard/trends?days=${days}`),
  getSourceDistribution: () => api.get<{ [key: string]: number }>('/api/dashboard/source-distribution')
};

export const alertsAPI = {
  getAlerts: (params?: any) => api.get<Alert[]>('/api/alerts', { params }),
  getAlertById: (id: string) => api.get<Alert>(`/api/alerts/${id}`),
  createAlert: (data: any) => api.post<Alert>('/api/alerts', data),
  resolveAlert: (id: string, notes: string) => 
    api.post<Alert>(`/api/alerts/${id}/resolve`, { resolution_notes: notes })
};

// Re-export types for convenience
export type {
  AlertSummary,
  TopOffender,
  RecentActivity,
  TrendDataPoint,
  Alert,
} from '../types';

export default api;

