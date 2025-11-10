/**
 * TypeScript interfaces for Alert Management System
 */

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

export interface Alert {
  alert_id: string;
  source_type: string;
  severity: string;
  status: string;
  timestamp: string;
  metadata: any;
  state_history?: StateTransition[];
  closed_at?: string;
  auto_close_reason?: string;
  resolved_by?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface StateTransition {
  from_status: string;
  to_status: string;
  timestamp: string;
  reason?: string;
  triggered_by?: string;
}

