# Alert Management Dashboard - Frontend

React TypeScript frontend for the Alert Management System.

## Setup Instructions

### 1. Create React App

```bash
npx create-react-app frontend --template typescript
cd frontend
```

### 2. Install Dependencies

```bash
npm install axios recharts react-router-dom lucide-react date-fns
```

### 3. Install Tailwind CSS

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 4. Start Development Server

```bash
npm start
```

The app will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── AlertSummaryCards.tsx
│   │   ├── TopOffendersTable.tsx
│   │   ├── RecentActivities.tsx
│   │   ├── TrendChart.tsx
│   │   ├── SourceDistributionChart.tsx
│   │   ├── AlertDetailModal.tsx
│   │   └── AutoClosedAlertsTable.tsx
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx
│   │   └── Login.tsx
│   ├── services/           # API services
│   │   └── api.ts
│   ├── types/              # TypeScript interfaces
│   │   └── index.ts
│   ├── App.tsx             # Main app with routing
│   ├── index.tsx           # Entry point
│   └── index.css           # Tailwind imports
├── tailwind.config.js       # Tailwind configuration
├── package.json
└── README.md
```

## Features

- ✅ **Authentication** - Login with JWT token
- ✅ **Dashboard** - Comprehensive alert analytics
- ✅ **Real-time Updates** - Auto-refresh every 30 seconds
- ✅ **Interactive Charts** - Recharts for data visualization
- ✅ **Responsive Design** - Mobile-first approach
- ✅ **Error Handling** - Graceful error states
- ✅ **Loading States** - Skeleton loaders
- ✅ **TypeScript** - Full type safety

## Default Credentials

- Username: `admin`
- Password: `Admin123!`

## API Configuration

The app connects to `http://localhost:8000` by default. The `proxy` setting in `package.json` handles CORS during development.

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

## Environment Variables

Create a `.env` file if you need to change the API URL:

```
REACT_APP_API_URL=http://localhost:8000
```

Then update `src/services/api.ts` to use `process.env.REACT_APP_API_URL`.

