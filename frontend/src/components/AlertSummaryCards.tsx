/**
 * AlertSummaryCards Component
 * Displays 4 summary cards with alert statistics
 */

import React from 'react';
import { Activity, AlertTriangle, AlertCircle, CheckCircle2 } from 'lucide-react';
import { AlertSummary } from '../types';

interface AlertSummaryCardsProps {
  data: AlertSummary | null;
  isLoading: boolean;
  error: Error | null;
}

const AlertSummaryCards: React.FC<AlertSummaryCardsProps> = ({ data, isLoading, error }) => {
  if (error) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="col-span-full bg-danger/10 border border-danger/20 rounded-lg p-4">
          <p className="text-danger text-sm">Error loading summary: {error.message}</p>
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
      color: 'text-primary',
      bgColor: 'bg-primary/10',
      borderColor: 'border-primary/20',
    },
    {
      title: 'Critical Alerts',
      value: data.critical_count,
      icon: AlertCircle,
      color: 'text-danger',
      bgColor: 'bg-danger/10',
      borderColor: 'border-danger/20',
      subValue: data.warning_count,
      subLabel: 'Warnings',
    },
    {
      title: 'Open Alerts',
      value: data.open_count,
      icon: AlertTriangle,
      color: 'text-warning',
      bgColor: 'bg-warning/10',
      borderColor: 'border-warning/20',
      subValue: data.escalated_count,
      subLabel: 'Escalated',
    },
    {
      title: 'Auto-Closed',
      value: data.auto_closed_count,
      icon: CheckCircle2,
      color: 'text-success',
      bgColor: 'bg-success/10',
      borderColor: 'border-success/20',
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
            className={`bg-white rounded-lg shadow-sm border ${card.borderColor} p-6 hover:shadow-md transition-shadow`}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">{card.title}</h3>
              <div className={`${card.bgColor} p-2 rounded-lg`}>
                <Icon className={`h-5 w-5 ${card.color}`} />
              </div>
            </div>
            <div className="flex items-baseline justify-between">
              <div>
                <p className={`text-3xl font-bold ${card.color}`}>
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

