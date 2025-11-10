/**
 * TopOffendersTable Component
 * Displays table of top drivers with most alerts
 */

import React from 'react';
import { TrendingUp, AlertCircle, Clock } from 'lucide-react';
import { TopOffender } from '../types';
import { formatDistanceToNow } from 'date-fns';

interface TopOffendersTableProps {
  data: TopOffender[] | null;
  isLoading: boolean;
  error: Error | null;
  onDriverClick?: (driverId: string) => void;
}

const TopOffendersTable: React.FC<TopOffendersTableProps> = ({
  data,
  isLoading,
  error,
  onDriverClick,
}) => {
  const getRankIcon = (index: number) => {
    switch (index) {
      case 0:
        return '🥇';
      case 1:
        return '🥈';
      case 2:
        return '🥉';
      default:
        return null;
    }
  };

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <AlertCircle className="h-12 w-12 text-danger mx-auto mb-4" />
          <p className="text-danger font-medium">Error loading top offenders</p>
          <p className="text-sm text-gray-500 mt-2">{error.message}</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Offenders</h2>
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
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Offenders</h2>
        <div className="text-center py-8">
          <p className="text-gray-500">No offenders found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Top Offenders</h2>
        <TrendingUp className="h-5 w-5 text-gray-400" />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rank
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Driver ID
              </th>
              <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total
              </th>
              <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Escalated
              </th>
              <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Open
              </th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Alert
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.map((offender, index) => (
              <tr
                key={offender.driver_id}
                className={`hover:bg-gray-50 transition-colors ${
                  offender.escalated_alerts > 0 ? 'bg-red-50/50' : ''
                } ${onDriverClick ? 'cursor-pointer' : ''}`}
                onClick={() => onDriverClick?.(offender.driver_id)}
              >
                <td className="py-4 px-4">
                  <div className="flex items-center">
                    {getRankIcon(index) ? (
                      <span className="text-2xl">{getRankIcon(index)}</span>
                    ) : (
                      <span
                        className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold ${
                          index < 3
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {index + 1}
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-4 px-4">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{offender.driver_id}</p>
                    {offender.driver_name && (
                      <p className="text-xs text-gray-500">{offender.driver_name}</p>
                    )}
                  </div>
                </td>
                <td className="py-4 px-4 text-center">
                  <span className="text-sm font-semibold text-gray-900">
                    {offender.total_alerts}
                  </span>
                </td>
                <td className="py-4 px-4 text-center">
                  {offender.escalated_alerts > 0 ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-danger/10 text-danger">
                      {offender.escalated_alerts}
                    </span>
                  ) : (
                    <span className="text-sm text-gray-400">0</span>
                  )}
                </td>
                <td className="py-4 px-4 text-center">
                  {offender.open_alerts > 0 ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-warning/10 text-warning">
                      {offender.open_alerts}
                    </span>
                  ) : (
                    <span className="text-sm text-gray-400">0</span>
                  )}
                </td>
                <td className="py-4 px-4 text-right">
                  <div className="flex items-center justify-end text-xs text-gray-500">
                    <Clock className="h-3 w-3 mr-1" />
                    {formatDistanceToNow(new Date(offender.last_alert_time), { addSuffix: true })}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TopOffendersTable;

