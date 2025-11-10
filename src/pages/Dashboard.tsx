/**
 * Dashboard Page
 * 
 * Main dashboard page composing all dashboard components
 */

import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';
import {
  dashboardAPI,
  alertsAPI,
  AlertSummary,
  TopOffender,
  RecentActivity,
  TrendDataPoint,
  SourceDistribution,
  Alert,
} from '../services/api';
import AlertSummaryCards from '../components/AlertSummaryCards';
import TopOffendersTable from '../components/TopOffendersTable';
import RecentActivities from '../components/RecentActivities';
import TrendChart from '../components/TrendChart';
import SourceDistributionChart from '../components/SourceDistributionChart';
import AutoClosedAlertsTable from '../components/AutoClosedAlertsTable';
import AlertDetailModal from '../components/AlertDetailModal';

const Dashboard = () => {
  // State management
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [topOffenders, setTopOffenders] = useState<TopOffender[] | null>(null);
  const [recentActivities, setRecentActivities] = useState<RecentActivity[] | null>(null);
  const [trends, setTrends] = useState<TrendDataPoint[] | null>(null);
  const [sourceDistribution, setSourceDistribution] = useState<SourceDistribution | null>(null);
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

  // Fetch all dashboard data
  const fetchDashboardData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) {
      setIsRefreshing(true);
    }

    // Fetch summary
    try {
      setLoading((prev) => ({ ...prev, summary: true }));
      setErrors((prev) => ({ ...prev, summary: null }));
      const summaryData = await dashboardAPI.getSummary();
      setSummary(summaryData);
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        summary: error instanceof Error ? error : new Error('Failed to load summary'),
      }));
    } finally {
      setLoading((prev) => ({ ...prev, summary: false }));
    }

    // Fetch top offenders
    try {
      setLoading((prev) => ({ ...prev, topOffenders: true }));
      setErrors((prev) => ({ ...prev, topOffenders: null }));
      const offendersData = await dashboardAPI.getTopOffenders(5);
      setTopOffenders(offendersData);
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        topOffenders: error instanceof Error ? error : new Error('Failed to load top offenders'),
      }));
    } finally {
      setLoading((prev) => ({ ...prev, topOffenders: false }));
    }

    // Fetch recent activities
    try {
      setLoading((prev) => ({ ...prev, recentActivities: true }));
      setErrors((prev) => ({ ...prev, recentActivities: null }));
      const activitiesData = await dashboardAPI.getRecentActivities(20);
      setRecentActivities(activitiesData);
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        recentActivities: error instanceof Error ? error : new Error('Failed to load activities'),
      }));
    } finally {
      setLoading((prev) => ({ ...prev, recentActivities: false }));
    }

    // Fetch trends
    try {
      setLoading((prev) => ({ ...prev, trends: true }));
      setErrors((prev) => ({ ...prev, trends: null }));
      const trendsData = await dashboardAPI.getTrends(7);
      setTrends(trendsData);
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        trends: error instanceof Error ? error : new Error('Failed to load trends'),
      }));
    } finally {
      setLoading((prev) => ({ ...prev, trends: false }));
    }

    // Fetch source distribution
    try {
      setLoading((prev) => ({ ...prev, sourceDistribution: true }));
      setErrors((prev) => ({ ...prev, sourceDistribution: null }));
      const distributionData = await dashboardAPI.getSourceDistribution();
      setSourceDistribution(distributionData);
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        sourceDistribution: error instanceof Error ? error : new Error('Failed to load distribution'),
      }));
    } finally {
      setLoading((prev) => ({ ...prev, sourceDistribution: false }));
    }

    // Fetch auto-closed alerts
    try {
      setLoading((prev) => ({ ...prev, autoClosed: true }));
      setErrors((prev) => ({ ...prev, autoClosed: null }));
      const autoClosedData = await dashboardAPI.getAutoClosed(24);
      setAutoClosed(autoClosedData);
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        autoClosed: error instanceof Error ? error : new Error('Failed to load auto-closed alerts'),
      }));
    } finally {
      setLoading((prev) => ({ ...prev, autoClosed: false }));
    }

    if (showRefreshing) {
      setIsRefreshing(false);
    }
  }, []);

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
      const alert = await alertsAPI.getAlert(alertId);
      setSelectedAlert(alert);
      setIsModalOpen(true);
    } catch (error) {
      console.error('Failed to load alert details:', error);
    }
  }, []);

  // Handle manual refresh
  const handleRefresh = useCallback(() => {
    fetchDashboardData(true);
  }, [fetchDashboardData]);

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
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw
                className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`}
              />
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </button>
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
          <TrendChart data={trends} isLoading={loading.trends} error={errors.trends} />
          <SourceDistributionChart
            data={sourceDistribution}
            isLoading={loading.sourceDistribution}
            error={errors.sourceDistribution}
          />
        </div>

        {/* Tables Row */}
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
          <AutoClosedAlertsTable
            data={autoClosed}
            isLoading={loading.autoClosed}
            error={errors.autoClosed}
            onAlertClick={handleAlertClick}
          />
        </div>

        {/* Recent Activities */}
        <div className="mb-8">
          <RecentActivities
            data={recentActivities}
            isLoading={loading.recentActivities}
            error={errors.recentActivities}
            onAlertClick={handleAlertClick}
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
      />
    </div>
  );
};

export default Dashboard;

