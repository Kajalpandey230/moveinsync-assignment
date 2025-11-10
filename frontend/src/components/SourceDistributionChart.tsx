/**
 * SourceDistributionChart Component
 * Pie chart (donut style) showing alert distribution by source type
 */

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { PieChart as PieChartIcon, AlertCircle } from 'lucide-react';
interface SourceDistribution {
  [key: string]: number;
}

interface SourceDistributionChartProps {
  data: SourceDistribution | null;
  isLoading: boolean;
  error: Error | null;
}

const COLORS = {
  OVERSPEEDING: '#ef4444', // danger
  COMPLIANCE: '#f59e0b', // warning
  DEFAULT: '#6b7280', // gray
};

const SourceDistributionChart: React.FC<SourceDistributionChartProps> = ({
  data,
  isLoading,
  error,
}) => {
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <AlertCircle className="h-12 w-12 text-danger mx-auto mb-4" />
          <p className="text-danger font-medium">Error loading source distribution</p>
          <p className="text-sm text-gray-500 mt-2">{error.message}</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Source Distribution</h2>
          <PieChartIcon className="h-5 w-5 text-gray-400" />
        </div>
        <div className="h-64 bg-gray-100 rounded animate-pulse"></div>
      </div>
    );
  }

  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Source Distribution</h2>
          <PieChartIcon className="h-5 w-5 text-gray-400" />
        </div>
        <div className="text-center py-8">
          <p className="text-gray-500">No data available</p>
        </div>
      </div>
    );
  }

  // Transform data for chart
  const chartData = Object.entries(data).map(([name, value]) => ({
    name: name.replace('_', ' '),
    value,
    color: COLORS[name as keyof typeof COLORS] || COLORS.DEFAULT,
  }));

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Source Distribution</h2>
        <PieChartIcon className="h-5 w-5 text-gray-400" />
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={5}
            dataKey="value"
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
            }}
            formatter={(value: number) => [
              `${value} (${((value / total) * 100).toFixed(1)}%)`,
              'Count',
            ]}
          />
          <Legend
            formatter={(value) => value.replace('_', ' ').toUpperCase()}
            iconType="circle"
            wrapperStyle={{ paddingTop: '20px' }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="mt-4 text-center">
        <p className="text-2xl font-bold text-gray-900">{total}</p>
        <p className="text-sm text-gray-500">Total Alerts</p>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4">
        {chartData.map((item) => (
          <div key={item.name} className="flex items-center justify-between">
            <div className="flex items-center">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: item.color }}
              ></div>
              <span className="text-sm text-gray-600">{item.name}</span>
            </div>
            <span className="text-sm font-semibold text-gray-900">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SourceDistributionChart;

