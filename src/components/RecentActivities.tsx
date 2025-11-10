/**
 * RecentActivities Component
 * 
 * Displays a timeline of recent alert lifecycle events
 */

import { Clock, AlertCircle, TrendingUp, CheckCircle2, XCircle, Activity } from 'lucide-react';
import { RecentActivity } from '../services/api';
import { formatDistanceToNow, format } from 'date-fns';

interface RecentActivitiesProps {
  data: RecentActivity[] | null;
  isLoading: boolean;
  error: Error | null;
  onAlertClick?: (alertId: string) => void;
}

const RecentActivities = ({ data, isLoading, error, onAlertClick }: RecentActivitiesProps) => {
  const getActionIcon = (action: string) => {
    switch (action) {
      case 'created':
        return <Activity className="h-4 w-4 text-blue-500" />;
      case 'escalated':
        return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'auto_closed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'resolved':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'created':
        return 'bg-blue-100 text-blue-800';
      case 'escalated':
        return 'bg-red-100 text-red-800';
      case 'auto_closed':
        return 'bg-green-100 text-green-800';
      case 'resolved':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800';
      case 'WARNING':
        return 'bg-yellow-100 text-yellow-800';
      case 'INFO':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 font-medium">Error loading recent activities</p>
          <p className="text-sm text-gray-500 mt-2">{error.message}</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h2>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse flex items-start space-x-4">
              <div className="h-8 w-8 bg-gray-200 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h2>
        <div className="text-center py-8">
          <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No recent activities</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h2>
      <div className="space-y-4">
        {data.map((activity, index) => (
          <div
            key={`${activity.alert_id}-${activity.timestamp}-${index}`}
            className={`flex items-start space-x-4 pb-4 ${
              index !== data.length - 1 ? 'border-b border-gray-200' : ''
            }`}
          >
            <div className="flex-shrink-0 mt-1">{getActionIcon(activity.action)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <button
                  onClick={() => onAlertClick?.(activity.alert_id)}
                  className={`text-sm font-medium text-gray-900 hover:text-blue-600 ${
                    onAlertClick ? 'cursor-pointer hover:underline' : ''
                  }`}
                >
                  {activity.alert_id}
                </button>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getActionColor(
                    activity.action
                  )}`}
                >
                  {activity.action.replace('_', ' ')}
                </span>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(
                    activity.severity
                  )}`}
                >
                  {activity.severity}
                </span>
              </div>
              <div className="flex items-center space-x-2 text-xs text-gray-500">
                <span className="capitalize">{activity.source_type.toLowerCase()}</span>
                {activity.driver_id && (
                  <>
                    <span>•</span>
                    <span>{activity.driver_id}</span>
                  </>
                )}
                <span>•</span>
                <div className="flex items-center">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                </div>
              </div>
              {activity.reason && (
                <p className="text-xs text-gray-600 mt-1 italic">{activity.reason}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentActivities;

