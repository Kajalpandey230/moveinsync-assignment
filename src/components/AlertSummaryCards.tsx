/**
 * AlertSummaryCards Component
 * 
 * Displays 4 summary cards showing total alerts, severity breakdown,
 * status breakdown, and auto-closed count
 */

import { AlertTriangle, Activity, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import { AlertSummary } from '../services/api';

interface AlertSummaryCardsProps {
  data: AlertSummary | null;
  isLoading: boolean;
  error: Error | null;
}

const AlertSummaryCards = ({ data, isLoading, error }: AlertSummaryCardsProps) => {
  if (error) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="col-span-full bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">Error loading summary: {error.message}</p>
        </div>
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Alerts',
      value: data.total_alerts,
      icon: Activity,
      color: 'bg-blue-500',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-700',
    },
    {
      title: 'Critical Alerts',
      value: data.critical_count,
      icon: AlertCircle,
      color: 'bg-red-500',
      bgColor: 'bg-red-50',
      textColor: 'text-red-700',
      subValue: data.warning_count,
      subLabel: 'Warnings',
    },
    {
      title: 'Open Alerts',
      value: data.open_count,
      icon: AlertTriangle,
      color: 'bg-yellow-500',
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-700',
      subValue: data.escalated_count,
      subLabel: 'Escalated',
    },
    {
      title: 'Auto-Closed',
      value: data.auto_closed_count,
      icon: CheckCircle2,
      color: 'bg-green-500',
      bgColor: 'bg-green-50',
      textColor: 'text-green-700',
      subValue: data.resolved_count,
      subLabel: 'Resolved',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.title}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">{card.title}</h3>
              <div className={`${card.color} p-2 rounded-lg`}>
                <Icon className="h-5 w-5 text-white" />
              </div>
            </div>
            <div className="flex items-baseline justify-between">
              <div>
                <p className={`text-3xl font-bold ${card.textColor}`}>
                  {card.value.toLocaleString()}
                </p>
                {card.subValue !== undefined && (
                  <p className="text-sm text-gray-500 mt-1">
                    {card.subValue} {card.subLabel}
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AlertSummaryCards;

