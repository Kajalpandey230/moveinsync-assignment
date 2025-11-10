/**
 * AutoClosedAlertsTable Component
 * Table of recently auto-closed alerts
 */

import React, { useState } from 'react';
import { CheckCircle2, AlertCircle, Clock, Eye } from 'lucide-react';
import { Alert } from '../types';
import { formatDistanceToNow } from 'date-fns';

interface AutoClosedAlertsTableProps {
  data: Alert[] | null;
  isLoading: boolean;
  error: Error | null;
  onAlertClick?: (alertId: string) => void;
  onTimeFilterChange?: (hours: number) => void;
}

const AutoClosedAlertsTable: React.FC<AutoClosedAlertsTableProps> = ({
  data,
  isLoading,
  error,
  onAlertClick,
  onTimeFilterChange,
}) => {
  const [timeFilter, setTimeFilter] = useState(24);

  const handleTimeFilterChange = (hours: number) => {
    setTimeFilter(hours);
    onTimeFilterChange?.(hours);
  };

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <AlertCircle className="h-12 w-12 text-danger mx-auto mb-4" />
          <p className="text-danger font-medium">Error loading auto-closed alerts</p>
          <p className="text-sm text-gray-500 mt-2">{error.message}</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Auto-Closed Alerts</h2>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-16 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Auto-Closed Alerts</h2>
          <CheckCircle2 className="h-5 w-5 text-gray-400" />
        </div>
        <div className="text-center py-8">
          <CheckCircle2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No auto-closed alerts in the selected time period</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Auto-Closed Alerts</h2>
        <div className="flex items-center space-x-2">
          <select
            value={timeFilter}
            onChange={(e) => handleTimeFilterChange(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-primary focus:border-primary"
          >
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last 7 days</option>
            <option value={720}>Last 30 days</option>
          </select>
          <CheckCircle2 className="h-5 w-5 text-success" />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Alert ID
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Source Type
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Driver ID
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Reason
              </th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Closed At
              </th>
              <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.map((alert) => (
              <tr
                key={alert.alert_id}
                className={`hover:bg-gray-50 transition-colors ${
                  onAlertClick ? 'cursor-pointer' : ''
                }`}
              >
                <td className="py-4 px-4">
                  <span className="text-sm font-mono text-gray-900">{alert.alert_id}</span>
                </td>
                <td className="py-4 px-4">
                  <span className="text-sm text-gray-900 capitalize">
                    {alert.source_type.toLowerCase()}
                  </span>
                </td>
                <td className="py-4 px-4">
                  <span className="text-sm text-gray-900">
                    {alert.metadata?.driver_id || 'N/A'}
                  </span>
                </td>
                <td className="py-4 px-4">
                  <p className="text-sm text-gray-700 max-w-xs truncate">
                    {alert.auto_close_reason || 'N/A'}
                  </p>
                </td>
                <td className="py-4 px-4 text-right">
                  <div className="flex items-center justify-end text-xs text-gray-500">
                    <Clock className="h-3 w-3 mr-1" />
                    {alert.closed_at
                      ? formatDistanceToNow(new Date(alert.closed_at), { addSuffix: true })
                      : 'N/A'}
                  </div>
                </td>
                <td className="py-4 px-4 text-center">
                  {onAlertClick && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onAlertClick(alert.alert_id);
                      }}
                      className="inline-flex items-center px-3 py-1 text-xs font-medium text-primary hover:text-primary/80 hover:bg-primary/10 rounded-md transition-colors"
                    >
                      <Eye className="h-3 w-3 mr-1" />
                      View
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AutoClosedAlertsTable;

