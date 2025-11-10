/**
 * TrendChart Component
 * Line chart showing alert trends over time
 */

import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, AlertCircle } from 'lucide-react';
import { TrendDataPoint } from '../types';
import { format, parseISO } from 'date-fns';

interface TrendChartProps {
  data: TrendDataPoint[] | null;
  isLoading: boolean;
  error: Error | null;
  onDaysChange?: (days: number) => void;
}

const TrendChart: React.FC<TrendChartProps> = ({ data, isLoading, error, onDaysChange }) => {
  const [days, setDays] = useState(7);

  const handleDaysChange = (newDays: number) => {
    setDays(newDays);
    onDaysChange?.(newDays);
  };

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <AlertCircle className="h-12 w-12 text-danger mx-auto mb-4" />
          <p className="text-danger font-medium">Error loading trend data</p>
          <p className="text-sm text-gray-500 mt-2">{error.message}</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Alert Trends</h2>
          <TrendingUp className="h-5 w-5 text-gray-400" />
        </div>
        <div className="h-64 bg-gray-100 rounded animate-pulse"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Alert Trends</h2>
          <TrendingUp className="h-5 w-5 text-gray-400" />
        </div>
        <div className="text-center py-8">
          <p className="text-gray-500">No trend data available</p>
        </div>
      </div>
    );
  }

  // Format data for chart
  const chartData = data.map((point) => ({
    ...point,
    date: format(parseISO(point.date), 'MMM dd'),
    fullDate: point.date,
  }));

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Alert Trends</h2>
        <div className="flex items-center space-x-2">
          <div className="flex rounded-md shadow-sm">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => handleDaysChange(d)}
                className={`px-3 py-1 text-sm font-medium ${
                  days === d
                    ? 'bg-primary text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                } border border-gray-300 first:rounded-l-md last:rounded-r-md first:border-r-0 last:border-l-0`}
              >
                {d}d
              </button>
            ))}
          </div>
          <TrendingUp className="h-5 w-5 text-gray-400" />
        </div>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            tick={{ fill: '#6b7280' }}
          />
          <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} tick={{ fill: '#6b7280' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
            }}
            labelFormatter={(label) => {
              const point = chartData.find((d) => d.date === label);
              return point ? format(parseISO(point.fullDate), 'MMMM dd, yyyy') : label;
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
            formatter={(value) => value.replace('_', ' ').toUpperCase()}
          />
          <Line
            type="monotone"
            dataKey="total_alerts"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 4 }}
            name="Total Alerts"
          />
          <Line
            type="monotone"
            dataKey="escalated"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ fill: '#ef4444', r: 4 }}
            name="Escalated"
          />
          <Line
            type="monotone"
            dataKey="auto_closed"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 4 }}
            name="Auto Closed"
          />
          <Line
            type="monotone"
            dataKey="resolved"
            stroke="#6b7280"
            strokeWidth={2}
            dot={{ fill: '#6b7280', r: 4 }}
            name="Resolved"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendChart;

