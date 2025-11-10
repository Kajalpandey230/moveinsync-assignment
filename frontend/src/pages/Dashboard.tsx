/**
 * Dashboard Page
 * Main dashboard composing all components
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, LogOut } from 'lucide-react';
import {
  dashboardAPI,
  alertsAPI,
  type AlertSummary,
  type TopOffender,
  type RecentActivity,
  type TrendDataPoint,
  type Alert,
} from '../services/api';
import AlertSummaryCards from '../components/AlertSummaryCards';
import TopOffendersTable from '../components/TopOffendersTable';
import RecentActivities from '../components/RecentActivities';
import TrendChart from '../components/TrendChart';
import SourceDistributionChart from '../components/SourceDistributionChart';
import AutoClosedAlertsTable from '../components/AutoClosedAlertsTable';
import AlertDetailModal from '../components/AlertDetailModal';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  
  // State management
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [topOffenders, setTopOffenders] = useState<TopOffender[] | null>(null);
  const [recentActivities, setRecentActivities] = useState<RecentActivity[] | null>(null);
  const [trends, setTrends] = useState<TrendDataPoint[] | null>(null);
  const [sourceDistribution, setSourceDistribution] = useState<{ [key: string]: number } | null>(null);
  const [autoClosed, setAutoClosed] = useState<Alert[] | null>(null);

  const [loading, setLoading] = useState({
    summary: true,
    topOffenders: true,
    recentActivities: true,
    trends: true,
    sourceDistribution: true,
    autoClosed: true,
  });

  const [errors, setErrors] = useState<{ [key: string]: Error | null }>({
    summary: null,
    topOffenders: null,
    recentActivities: null,
    trends: null,
    sourceDistribution: null,
    autoClosed: null,
  });

  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [autoClosedHours, setAutoClosedHours] = useState(24);
  const [trendDays, setTrendDays] = useState(7);

  // Fetch all dashboard data
  const fetchDashboardData = useCallback(
    async (showRefreshing = false) => {
      if (showRefreshing) {
        setIsRefreshing(true);
      }

      // Fetch summary
      try {
        setLoading((prev) => ({ ...prev, summary: true }));
        setErrors((prev) => ({ ...prev, summary: null }));
        const response = await dashboardAPI.getSummary();
        setSummary(response.data);
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load summary';
        const errorText = Array.isArray(errorMessage) 
          ? errorMessage.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
          : (typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
        setErrors((prev) => ({
          ...prev,
          summary: new Error(errorText),
        }));
      } finally {
        setLoading((prev) => ({ ...prev, summary: false }));
      }

      // Fetch top offenders
      try {
        setLoading((prev) => ({ ...prev, topOffenders: true }));
        setErrors((prev) => ({ ...prev, topOffenders: null }));
        const response = await dashboardAPI.getTopOffenders(5);
        setTopOffenders(response.data);
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load top offenders';
        const errorText = Array.isArray(errorMessage) 
          ? errorMessage.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
          : (typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
        setErrors((prev) => ({
          ...prev,
          topOffenders: new Error(errorText),
        }));
      } finally {
        setLoading((prev) => ({ ...prev, topOffenders: false }));
      }

      // Fetch recent activities
      try {
        setLoading((prev) => ({ ...prev, recentActivities: true }));
        setErrors((prev) => ({ ...prev, recentActivities: null }));
        const response = await dashboardAPI.getRecentActivities(20);
        setRecentActivities(response.data);
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load activities';
        const errorText = Array.isArray(errorMessage) 
          ? errorMessage.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
          : (typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
        setErrors((prev) => ({
          ...prev,
          recentActivities: new Error(errorText),
        }));
      } finally {
        setLoading((prev) => ({ ...prev, recentActivities: false }));
      }

      // Fetch trends
      try {
        setLoading((prev) => ({ ...prev, trends: true }));
        setErrors((prev) => ({ ...prev, trends: null }));
        const response = await dashboardAPI.getTrends(trendDays);
        setTrends(response.data);
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load trends';
        const errorText = Array.isArray(errorMessage) 
          ? errorMessage.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
          : (typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
        setErrors((prev) => ({
          ...prev,
          trends: new Error(errorText),
        }));
      } finally {
        setLoading((prev) => ({ ...prev, trends: false }));
      }

      // Fetch source distribution
      try {
        setLoading((prev) => ({ ...prev, sourceDistribution: true }));
        setErrors((prev) => ({ ...prev, sourceDistribution: null }));
        const response = await dashboardAPI.getSourceDistribution();
        setSourceDistribution(response.data);
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load distribution';
        const errorText = Array.isArray(errorMessage) 
          ? errorMessage.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
          : (typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
        setErrors((prev) => ({
          ...prev,
          sourceDistribution: new Error(errorText),
        }));
      } finally {
        setLoading((prev) => ({ ...prev, sourceDistribution: false }));
      }

      // Fetch auto-closed alerts
      try {
        setLoading((prev) => ({ ...prev, autoClosed: true }));
        setErrors((prev) => ({ ...prev, autoClosed: null }));
        const response = await dashboardAPI.getAutoClosedAlerts(autoClosedHours);
        setAutoClosed(response.data);
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load auto-closed alerts';
        const errorText = Array.isArray(errorMessage) 
          ? errorMessage.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
          : (typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
        setErrors((prev) => ({
          ...prev,
          autoClosed: new Error(errorText),
        }));
      } finally {
        setLoading((prev) => ({ ...prev, autoClosed: false }));
      }

      if (showRefreshing) {
        setIsRefreshing(false);
      }
    },
    [autoClosedHours, trendDays]
  );

  // Initial load
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  // Handle alert click
  const handleAlertClick = useCallback(async (alertId: string) => {
    try {
      const response = await alertsAPI.getAlertById(alertId);
      setSelectedAlert(response.data);
      setIsModalOpen(true);
    } catch (error) {
      console.error('Failed to load alert details:', error);
    }
  }, []);

  // Handle manual refresh
  const handleRefresh = useCallback(() => {
    fetchDashboardData(true);
  }, [fetchDashboardData]);

  // Handle auto-closed time filter change
  const handleAutoClosedTimeFilter = useCallback((hours: number) => {
    setAutoClosedHours(hours);
  }, []);

  // Handle alert resolved
  const handleAlertResolved = useCallback(() => {
    fetchDashboardData(true);
  }, [fetchDashboardData]);

  // Handle logout
  const handleLogout = useCallback(() => {
    localStorage.removeItem('token');
    navigate('/login');
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Alert Management Dashboard</h1>
              <p className="mt-1 text-sm text-gray-500">
                Real-time monitoring and analytics for alert system
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'Refreshing...' : 'Refresh'}
              </button>
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-4 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        <div className="mb-8">
          <AlertSummaryCards
            data={summary}
            isLoading={loading.summary}
            error={errors.summary}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <TopOffendersTable
            data={topOffenders}
            isLoading={loading.topOffenders}
            error={errors.topOffenders}
            onDriverClick={(driverId) => {
              // Could navigate to driver detail page or filter alerts
              console.log('Driver clicked:', driverId);
            }}
          />
          <SourceDistributionChart
            data={sourceDistribution}
            isLoading={loading.sourceDistribution}
            error={errors.sourceDistribution}
          />
        </div>

        {/* Trend Chart */}
        <div className="mb-8">
          <TrendChart
            data={trends}
            isLoading={loading.trends}
            error={errors.trends}
            onDaysChange={setTrendDays}
          />
        </div>

        {/* Tables Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <RecentActivities
            data={recentActivities}
            isLoading={loading.recentActivities}
            error={errors.recentActivities}
            onAlertClick={handleAlertClick}
          />
          <AutoClosedAlertsTable
            data={autoClosed}
            isLoading={loading.autoClosed}
            error={errors.autoClosed}
            onAlertClick={handleAlertClick}
            onTimeFilterChange={handleAutoClosedTimeFilter}
          />
        </div>
      </div>

      {/* Alert Detail Modal */}
      <AlertDetailModal
        alert={selectedAlert}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedAlert(null);
        }}
        onResolved={handleAlertResolved}
      />
    </div>
  );
};

export default Dashboard;

