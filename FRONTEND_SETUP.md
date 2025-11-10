# Frontend Setup Guide

## Overview

This is a React + TypeScript dashboard for the Alert Management System, built with:
- React 18 with TypeScript
- Tailwind CSS for styling
- Recharts for data visualization
- Lucide React for icons
- Axios for API calls
- React Router for routing

## Installation

1. **Install dependencies:**
```bash
npm install
```

2. **Create environment file:**
Create a `.env` file in the root directory:
```env
VITE_API_BASE_URL=http://localhost:8000
```

3. **Start development server:**
```bash
npm run dev
```

The app will be available at `http://localhost:5173` (or the port Vite assigns).

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── AlertSummaryCards.tsx
│   ├── TopOffendersTable.tsx
│   ├── RecentActivities.tsx
│   ├── TrendChart.tsx
│   ├── SourceDistributionChart.tsx
│   ├── AlertDetailModal.tsx
│   └── AutoClosedAlertsTable.tsx
├── pages/              # Page components
│   └── Dashboard.tsx
├── services/           # API services
│   └── api.ts
└── App.tsx            # Main app component with routing
```

## Features

### Dashboard Components

1. **AlertSummaryCards** - 4 summary cards showing:
   - Total alerts
   - Critical alerts (with warnings)
   - Open alerts (with escalated)
   - Auto-closed (with resolved)

2. **TopOffendersTable** - Table of top 5 drivers with:
   - Total alerts count
   - Escalated alerts
   - Open alerts
   - Last alert time

3. **RecentActivities** - Timeline of recent alert events:
   - Alert creation
   - Escalations
   - Auto-closures
   - Resolutions

4. **TrendChart** - Line chart showing:
   - Daily alert trends
   - Escalated alerts
   - Auto-closed alerts
   - Resolved alerts

5. **SourceDistributionChart** - Pie chart showing:
   - Alert distribution by source type
   - Percentage breakdown

6. **AutoClosedAlertsTable** - Table of recently auto-closed alerts:
   - Alert details
   - Auto-close reason
   - Closed timestamp

7. **AlertDetailModal** - Modal showing:
   - Full alert details
   - State history
   - Metadata
   - Resolution information

### Features

- ✅ **Auto-refresh** - Data refreshes every 30 seconds
- ✅ **Manual refresh** - Click refresh button to update data
- ✅ **Loading states** - Skeleton loaders while fetching
- ✅ **Error handling** - Graceful error messages with retry
- ✅ **Responsive design** - Mobile-first, works on all screen sizes
- ✅ **Interactive elements** - Clickable alerts, hover effects
- ✅ **Color-coded indicators** - Severity and status colors
- ✅ **Accessibility** - Proper ARIA labels and keyboard navigation

## API Integration

The dashboard integrates with these endpoints:

- `GET /api/dashboard/summary` - Alert summary statistics
- `GET /api/dashboard/top-offenders?limit=5` - Top offenders
- `GET /api/dashboard/trends?days=7` - Trend data
- `GET /api/dashboard/source-distribution` - Source distribution
- `GET /api/dashboard/recent-activities?limit=20` - Recent activities
- `GET /api/dashboard/auto-closed?hours=24` - Auto-closed alerts
- `GET /api/alerts/{alert_id}` - Alert details

## Authentication

The API client automatically includes the JWT token from localStorage. Make sure to:
1. Login first to get a token
2. Token is stored in localStorage as `auth_token`
3. Token is automatically included in all API requests

## Color Scheme

- **Critical/Error**: Red (#ef4444)
- **Warning**: Yellow/Orange (#f59e0b)
- **Info**: Blue (#3b82f6)
- **Success**: Green (#10b981)
- **Neutral**: Gray (#6b7280)

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Development Notes

- All components are fully typed with TypeScript
- Components handle loading, error, and empty states
- API errors are caught and displayed gracefully
- Auto-refresh can be disabled by removing the useEffect interval
- All date formatting uses `date-fns` library

## Troubleshooting

### CORS Issues
If you encounter CORS errors, make sure:
1. Backend CORS is configured to allow your frontend origin
2. API base URL is correct in `.env` file

### Authentication Issues
If API calls fail with 401:
1. Check if token exists in localStorage
2. Verify token is valid (not expired)
3. Login again to get a new token

### Chart Not Rendering
If Recharts components don't render:
1. Check browser console for errors
2. Verify data format matches expected structure
3. Ensure ResponsiveContainer has proper dimensions

