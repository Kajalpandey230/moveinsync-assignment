# Frontend Setup Instructions

## Step-by-Step Setup

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

This will create:
- `tailwind.config.js`
- `postcss.config.js`

### 4. Configure Tailwind

The `tailwind.config.js` file is already configured. Make sure `src/index.css` has:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 5. Start Development Server

```bash
npm start
```

The app will open at `http://localhost:3000`

## Project Structure

All files have been created in the `frontend/` directory:

```
frontend/
├── src/
│   ├── components/          # 7 components
│   ├── pages/               # Dashboard & Login
│   ├── services/            # API service
│   ├── types/               # TypeScript interfaces
│   ├── App.tsx              # Routing
│   ├── index.tsx            # Entry point
│   └── index.css            # Tailwind imports
├── tailwind.config.js
├── postcss.config.js
├── package.json
└── README.md
```

## Features Implemented

✅ **7 Components:**
- AlertSummaryCards - 4 summary cards
- TopOffendersTable - Top 5 drivers with rank medals
- RecentActivities - Timeline with auto-scroll
- TrendChart - Line chart with time range selector
- SourceDistributionChart - Donut pie chart
- AlertDetailModal - Full-screen modal with resolve
- AutoClosedAlertsTable - Table with time filter

✅ **Pages:**
- Dashboard - Main dashboard page
- Login - Authentication page

✅ **Features:**
- Auto-refresh every 30 seconds
- Manual refresh button
- Loading states (skeletons)
- Error handling with retry
- Empty states
- Responsive design
- TypeScript types
- Accessibility (ARIA labels)

## Default Credentials

- **Username:** `admin`
- **Password:** `Admin123!`

## API Configuration

The app connects to `http://localhost:8000` by default. The `proxy` setting in `package.json` handles CORS during development.

## Troubleshooting

### CORS Issues
If you see CORS errors, make sure:
1. Backend is running on port 8000
2. Backend CORS is configured to allow `http://localhost:3000`
3. `proxy` is set in `package.json`

### TypeScript Errors
If you see TypeScript errors:
1. Make sure all dependencies are installed
2. Run `npm install` again
3. Check that `tsconfig.json` is properly configured

### Build Errors
If build fails:
1. Delete `node_modules` and `package-lock.json`
2. Run `npm install` again
3. Check Node.js version (should be 16+)

## Next Steps

1. Start the backend server on port 8000
2. Run `npm start` in the frontend directory
3. Login with default credentials
4. Explore the dashboard!

