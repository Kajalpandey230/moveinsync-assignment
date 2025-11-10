/**
 * API service for Alert Management System
 * 
 * Provides typed functions for all API endpoints with error handling
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export interface AlertSummary {
  total_alerts: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  open_count: number;
  escalated_count: number;
  auto_closed_count: number;
  resolved_count: number;
}

export interface TopOffender {
  driver_id: string;
  driver_name?: string;
  open_alerts: number;
  escalated_alerts: number;
  total_alerts: number;
  last_alert_time: string;
}

export interface RecentActivity {
  alert_id: string;
  source_type: string;
  severity: string;
  status: string;
  driver_id?: string;
  timestamp: string;
  action: string;
  reason?: string;
}

export interface TrendDataPoint {
  date: string;
  total_alerts: number;
  escalated: number;
  auto_closed: number;
  resolved: number;
}

export interface SourceDistribution {
  [sourceType: string]: number;
}

export interface Alert {
  alert_id: string;
  source_type: string;
  severity: string;
  status: string;
  timestamp: string;
  metadata: {
    driver_id?: string;
    vehicle_id?: string;
    [key: string]: any;
  };
  state_history?: Array<{
    from_status: string;
    to_status: string;
    timestamp: string;
    reason?: string;
    triggered_by?: string;
  }>;
  closed_at?: string;
  auto_close_reason?: string;
  resolved_by?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface ResolveAlertRequest {
  resolution_notes: string;
}

// ============================================================================
// API CLIENT SETUP
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// AUTH API
// ============================================================================

export const authAPI = {
  login: async (username: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    const token = response.data.access_token;
    localStorage.setItem('auth_token', token);
    
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('auth_token');
  },
  
  getToken: (): string | null => {
    return localStorage.getItem('auth_token');
  },
};

// ============================================================================
// DASHBOARD API
// ============================================================================

export const dashboardAPI = {
  /**
   * Get overall alert summary statistics
   */
  getSummary: async (): Promise<AlertSummary> => {
    const response = await apiClient.get<AlertSummary>('/api/dashboard/summary');
    return response.data;
  },

  /**
   * Get top N drivers with most active alerts
   */
  getTopOffenders: async (limit: number = 5): Promise<TopOffender[]> => {
    const response = await apiClient.get<TopOffender[]>(
      `/api/dashboard/top-offenders?limit=${limit}`
    );
    return response.data;
  },

  /**
   * Get recent alert lifecycle events
   */
  getRecentActivities: async (limit: number = 20): Promise<RecentActivity[]> => {
    const response = await apiClient.get<RecentActivity[]>(
      `/api/dashboard/recent-activities?limit=${limit}`
    );
    return response.data;
  },

  /**
   * Get daily alert trend data
   */
  getTrends: async (days: number = 7): Promise<TrendDataPoint[]> => {
    const response = await apiClient.get<TrendDataPoint[]>(
      `/api/dashboard/trends?days=${days}`
    );
    return response.data;
  },

  /**
   * Get alert distribution by source type
   */
  getSourceDistribution: async (): Promise<SourceDistribution> => {
    const response = await apiClient.get<SourceDistribution>(
      '/api/dashboard/source-distribution'
    );
    return response.data;
  },

  /**
   * Get recently auto-closed alerts
   */
  getAutoClosed: async (hours: number = 24): Promise<Alert[]> => {
    const response = await apiClient.get<Alert[]>(
      `/api/dashboard/auto-closed?hours=${hours}`
    );
    return response.data;
  },
};

// ============================================================================
// ALERTS API
// ============================================================================

export const alertsAPI = {
  /**
   * Get alert by ID
   */
  getAlert: async (alertId: string): Promise<Alert> => {
    const response = await apiClient.get<Alert>(`/api/alerts/${alertId}`);
    return response.data;
  },

  /**
   * Resolve an alert
   */
  resolveAlert: async (alertId: string, resolutionNotes: string): Promise<Alert> => {
    const response = await apiClient.post<Alert>(
      `/api/alerts/${alertId}/resolve`,
      { resolution_notes: resolutionNotes }
    );
    return response.data;
  },
};

// ============================================================================
// ERROR HANDLING UTILITIES
// ============================================================================

export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>;
    return axiosError.response?.data?.detail || axiosError.message || 'An error occurred';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

