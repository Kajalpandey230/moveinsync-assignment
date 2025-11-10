move in sync assignment

# 🚨 Intelligent Alert Escalation & Resolution System

A sophisticated alert management platform designed for fleet monitoring operations that automatically escalates, de-escalates, and closes alerts based on dynamic, configurable rules while providing real-time analytics through an interactive dashboard.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [API Documentation](#-api-documentation)
- [Rule Engine](#-rule-engine)
- [Dashboard Features](#-dashboard-features)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Design Decisions](#-design-decisions)
- [Performance Optimization](#-performance-optimization)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

This system addresses the challenge of managing alerts from multiple fleet-monitoring modules (Safety, Compliance, Feedback). Instead of manual review, it provides:

- **Intelligent Auto-Escalation**: Automatically escalates alerts to CRITICAL when rule thresholds are met (e.g., 3 overspeeding incidents within 1 hour)
- **Smart Auto-Closure**: Background worker automatically closes alerts when conditions are satisfied (e.g., document renewed, time window expired)
- **Real-time Dashboard**: Interactive analytics showing alert trends, top offenders, and system health
- **Configurable Rules**: JSON/YAML-based rule engine that can be updated without code changes

### Problem Statement

MoveInSync operates multiple fleet-monitoring modules generating alerts like overspeeding, expiring documents, and poor driver feedback. These alerts were previously static and required manual review. The operations team needed a smart alert engine that could:

1. Automatically escalate based on frequency/severity patterns
2. Auto-close alerts when conditions are met
3. Provide real-time visibility into alert trends
4. Support configurable business rules

---

## ✨ Key Features

### 🔔 Alert Management
- **Multi-Source Ingestion**: Accepts alerts from Safety, Compliance, Feedback modules via REST API
- **Unified Data Model**: Normalizes alerts into consistent structure with `{alertId, sourceType, severity, timestamp, status, metadata}`
- **State Machine**: Manages alert lifecycle → `OPEN → ESCALATED → AUTO-CLOSED → RESOLVED`
- **Manual Resolution**: Operators can manually resolve alerts with notes

### 🤖 Rule Engine
- **Dynamic Rules**: JSON-based configuration for escalation and auto-closure rules
- **Count-Based Escalation**: "Escalate if 3 overspeeding alerts within 60 minutes"
- **Condition-Based Closure**: "Auto-close if document_valid == true"
- **Time-Based Expiry**: Alerts expire after configurable time windows
- **Rule Decoupling**: Update rules without redeploying code

### ⏰ Background Processing
- **Periodic Scanner**: Runs every 5 minutes to check auto-close conditions
- **Idempotent Operations**: Safe to run multiple times without side effects
- **Job Tracking**: Logs execution statistics (alerts processed, closed, errors)
- **Fault Tolerance**: Continues processing even if individual alerts fail

### 📊 Interactive Dashboard
- **Alert Summary Cards**: Total alerts, by severity, by status
- **Top Offenders**: Leaderboard of drivers with most open/escalated alerts
- **Trend Analysis**: Line charts showing daily alert patterns
- **Source Distribution**: Pie chart of alerts by type
- **Recent Activities**: Timeline of alert state transitions
- **Auto-Closed Transparency**: Recent auto-closures with reasons
- **Alert Drill-Down**: Click any alert to view full history and metadata

### 🔐 Security
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control (RBAC)**: Admin, Operator, Viewer roles
- **Protected Endpoints**: All APIs require authentication
- **Password Hashing**: bcrypt for secure password storage

---

## 🏗️ System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dashboard │  │  Charts  │  │  Tables  │  │  Modals  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Auth Routes  │  │ Alert Routes │  │Dashboard APIs│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Rule Engine  │  │Alert Service │  │Job Scheduler │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    MongoDB Database                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Users   │  │  Alerts  │  │  Rules   │  │   Jobs   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
                    ┌───────┴────────┐
                    │ APScheduler    │
                    │ (Every 5 mins) │
                    └────────────────┘
```

### Data Flow

1. **Alert Creation**: POST /api/alerts → Alert Service → MongoDB → Rule Engine checks escalation
2. **Auto-Closure**: APScheduler → Background Job → Rule Engine evaluates → Update alerts
3. **Dashboard**: React → API calls → Dashboard Service → MongoDB aggregations → Charts
4. **Authentication**: Login → JWT token → Stored in localStorage → Sent with all requests

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.104+ (Python 3.9+)
  - High performance, async/await support
  - Automatic OpenAPI documentation
  - Type validation with Pydantic

- **Database**: MongoDB 6.0+
  - Flexible schema for varied alert metadata
  - Powerful aggregation pipeline for analytics
  - Horizontal scalability

- **Authentication**: 
  - JWT (python-jose)
  - Password hashing (passlib with bcrypt)

- **Background Jobs**: APScheduler 3.10+
  - Lightweight in-process scheduler
  - Interval-based job triggers

- **ODM**: Motor 3.3+ (async MongoDB driver)
  - Native async/await support
  - Connection pooling

### Frontend
- **Framework**: React 18+ with TypeScript
  - Type safety
  - Component reusability
  - Modern hooks-based architecture

- **Styling**: Tailwind CSS 3.3+
  - Utility-first CSS
  - Responsive design
  - Consistent design system

- **Charts**: Recharts 2.10+
  - Line charts for trends
  - Pie charts for distribution
  - Responsive and interactive

- **HTTP Client**: Axios 1.6+
  - Promise-based
  - Request/response interceptors for auth

- **Icons**: Lucide React 0.263+
  - Modern, consistent icon set

- **Date Handling**: date-fns 2.30+
  - Lightweight date utilities

### Development Tools
- **API Testing**: pytest, requests
- **Code Quality**: Black (formatter), mypy (type checker)
- **Version Control**: Git
- **Environment Management**: python-dotenv

---

## 📁 Project Structure
```
moveinsync-assignment/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── database.py                  # MongoDB connection setup
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py               # Pydantic models (AlertModel, RuleModel, UserModel)
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py           # JWT token creation/validation
│   │   ├── password_utils.py        # Password hashing utilities
│   │   └── dependencies.py          # Auth dependencies (get_current_user, RBAC)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── alert_service.py         # Alert CRUD operations
│   │   ├── rule_service.py          # Rule management
│   │   ├── rule_engine.py           # Core escalation/auto-close logic
│   │   ├── dashboard_service.py     # Dashboard aggregations
│   │   └── job_service.py           # Background job tracking
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py           # Authentication endpoints
│   │   ├── alert_routes.py          # Alert management endpoints
│   │   ├── rule_routes.py           # Rule configuration endpoints
│   │   └── dashboard_routes.py      # Dashboard data endpoints
│   │
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── scheduler.py             # APScheduler setup
│   │   └── auto_close_job.py        # Auto-closure background job
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── alert_id_generator.py    # Generate unique alert IDs
│   │
│   └── config/
│       ├── __init__.py
│       ├── settings.py              # Environment configuration
│       └── default_rules.json       # Default rule definitions
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AlertSummaryCards.tsx
│   │   │   ├── TopOffendersTable.tsx
│   │   │   ├── RecentActivities.tsx
│   │   │   ├── TrendChart.tsx
│   │   │   ├── SourceDistributionChart.tsx
│   │   │   ├── AlertDetailModal.tsx
│   │   │   └── AutoClosedAlertsTable.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   └── Login.tsx
│   │   │
│   │   ├── services/
│   │   │   └── api.ts               # Axios API client
│   │   │
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript interfaces
│   │   │
│   │   ├── App.tsx
│   │   └── index.tsx
│   │
│   ├── package.json
│   └── tailwind.config.js
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py                  # API endpoint tests
│   ├── test_rule_engine.py          # Rule engine unit tests
│   └── conftest.py                  # Pytest fixtures
│
├── scripts/
│   ├── create_admin.py              # Create admin user
│   ├── seed_data.py                 # Populate test data
│   ├── quick_test.py                # Quick API testing script
│   └── test_phase3.py               # Phase 3 integration tests
│
├── docs/
│   ├── api_documentation.md         # Complete API reference
│   ├── architecture.md              # System design document
│   ├── trade_offs.md                # Design decisions and trade-offs
│   └── complexity_analysis.md       # Time/space complexity analysis
│
├── .env.example                     # Environment variables template
├── .gitignore
├── requirements.txt                 # Python dependencies
├── README.md
└── pytest.ini                       # Pytest configuration
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9 or higher
- Node.js 16 or higher
- MongoDB 6.0 or higher
- Git

### Backend Setup

1. **Clone the repository**
```bash
   git clone https://github.com/yourusername/moveinsync-assignment.git
   cd moveinsync-assignment
```

2. **Create virtual environment**
```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
   cp .env.example .env
```
   
   Edit `.env` and set:
```env
   # MongoDB
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=alert_system
   
   # JWT
   SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   
   # Application
   ENVIRONMENT=development
   LOG_LEVEL=INFO
```

5. **Generate SECRET_KEY**
```bash
   # Windows PowerShell
   python -c "import secrets; print(secrets.token_hex(32))"
   
   # Linux/Mac
   openssl rand -hex 32
```

6. **Start MongoDB**
```bash
   # Make sure MongoDB is running
   # Windows: MongoDB should be running as a service
   # Linux/Mac: mongod --dbpath /path/to/data
```

7. **Create admin user**
```bash
   python scripts/create_admin.py
```
   
   Default credentials:
   - Username: `admin`
   - Password: `Admin123!`

8. **Load default rules**
```bash
   # Rules will be loaded automatically on first API call
   # Or manually via: POST /api/rules/load-defaults
```

9. **Start backend server**
```bash
   uvicorn app.main:app --reload
```
   
   Backend will run at: `http://localhost:8000`
   API docs available at: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
   cd frontend
```

2. **Install dependencies**
```bash
   npm install
```

3. **Start development server**
```bash
   npm start
```
   
   Frontend will open at: `http://localhost:3000`

### Quick Start with Sample Data
```bash
# Seed database with test data
python scripts/seed_data.py

# Run demo scenario
python scripts/quick_test.py
```

---

## 📚 API Documentation

### Authentication Endpoints

#### POST `/auth/login`
Login and receive JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "Admin123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### GET `/auth/me`
Get current user profile (requires auth).

**Response:**
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "role": "ADMIN",
  "is_active": true
}
```

### Alert Endpoints

#### POST `/api/alerts`
Create new alert (requires OPERATOR role).

**Request:**
```json
{
  "source_type": "OVERSPEEDING",
  "metadata": {
    "driver_id": "DRV001",
    "vehicle_id": "VEH123",
    "speed": 85.5,
    "speed_limit": 60.0,
    "location": "MG Road, Bangalore"
  }
}
```

**Response:**
```json
{
  "alert_id": "OSP-2025-00001",
  "source_type": "OVERSPEEDING",
  "severity": "WARNING",
  "status": "OPEN",
  "timestamp": "2025-11-10T10:30:00Z",
  "metadata": {...}
}
```

#### GET `/api/alerts`
List alerts with filters (requires VIEWER role).

**Query Parameters:**
- `status`: Filter by status (OPEN, ESCALATED, AUTO_CLOSED, RESOLVED)
- `source_type`: Filter by source
- `severity`: Filter by severity
- `driver_id`: Filter by driver
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (default: 50, max: 100)

**Response:**
```json
{
  "alerts": [...],
  "total": 150,
  "skip": 0,
  "limit": 50
}
```

#### GET `/api/alerts/{alert_id}`
Get single alert details (requires VIEWER role).

**Response:**
```json
{
  "alert_id": "OSP-2025-00001",
  "status": "ESCALATED",
  "severity": "CRITICAL",
  "state_history": [
    {
      "from_status": "OPEN",
      "to_status": "ESCALATED",
      "timestamp": "2025-11-10T10:35:00Z",
      "reason": "3 overspeeding incidents within 60 minutes",
      "triggered_by": "system",
      "rule_triggered": "RULE-OVERSPEED-001"
    }
  ]
}
```

#### POST `/api/alerts/{alert_id}/resolve`
Manually resolve an alert (requires OPERATOR role).

**Request:**
```json
{
  "resolution_notes": "Contacted driver, issued warning"
}
```

### Dashboard Endpoints

#### GET `/api/dashboard/summary`
Get overall alert statistics.

**Response:**
```json
{
  "total_alerts": 1250,
  "critical_count": 45,
  "warning_count": 234,
  "info_count": 971,
  "open_count": 123,
  "escalated_count": 45,
  "auto_closed_count": 890,
  "resolved_count": 192
}
```

#### GET `/api/dashboard/top-offenders?limit=5`
Get drivers with most alerts.

**Response:**
```json
[
  {
    "driver_id": "DRV001",
    "open_alerts": 12,
    "escalated_alerts": 5,
    "total_alerts": 45,
    "last_alert_time": "2025-11-10T10:30:00Z"
  }
]
```

#### GET `/api/dashboard/trends?days=7`
Get daily trend data.

**Response:**
```json
[
  {
    "date": "2025-11-10",
    "total_alerts": 45,
    "escalated": 5,
    "auto_closed": 30,
    "resolved": 10
  }
]
```

### Rule Endpoints

#### GET `/api/rules`
List all rules (requires VIEWER role).

#### POST `/api/rules`
Create new rule (requires ADMIN role).

#### PUT `/api/rules/{rule_id}`
Update rule (requires ADMIN role).

#### POST `/api/rules/load-defaults`
Load default rules from JSON (requires ADMIN role).

For complete API documentation, visit: `http://localhost:8000/docs` (Swagger UI)

---

## 🎯 Rule Engine

### Rule Structure

Rules are defined in JSON format in `app/config/default_rules.json`:
```json
{
  "rule_id": "RULE-OVERSPEED-001",
  "source_type": "OVERSPEEDING",
  "name": "Overspeeding Critical Escalation",
  "description": "Escalate to CRITICAL if driver has 3+ overspeeding incidents within 1 hour",
  "conditions": {
    "escalate_if_count": 3,
    "window_mins": 60,
    "expire_after_mins": 1440
  },
  "is_active": true,
  "priority": 1
}
```

### Rule Types

#### 1. Count-Based Escalation
Escalates when threshold is reached within time window.

**Example:** 3 overspeeding alerts in 60 minutes → ESCALATED
```json
{
  "escalate_if_count": 3,
  "window_mins": 60
}
```

#### 2. Condition-Based Auto-Closure
Closes alert when metadata condition is met.

**Example:** Document renewed (document_valid = true) → AUTO_CLOSED
```json
{
  "auto_close_if": "document_valid"
}
```

#### 3. Time-Based Expiry
Alert expires after configured time.

**Example:** Alert auto-closes after 7 days → AUTO_CLOSED
```json
{
  "expire_after_mins": 10080
}
```

### Rule Evaluation Logic

1. **Real-time Escalation** (on alert creation):
```
   POST /api/alerts → Create Alert → Rule Engine checks escalation rules
   → If threshold met → Update status to ESCALATED, severity to CRITICAL
```

2. **Periodic Auto-Closure** (every 5 minutes):
```
   Background Job → Query OPEN/ESCALATED alerts → For each alert:
   → Check auto-close conditions → If met → Update status to AUTO_CLOSED
```

### Adding Custom Rules

1. **Via API** (ADMIN role required):
```bash
   POST /api/rules
   {
     "rule_id": "RULE-CUSTOM-001",
     "source_type": "SAFETY",
     "conditions": {
       "escalate_if_count": 2,
       "window_mins": 120
     }
   }
```

2. **Via JSON file**:
   - Edit `app/config/default_rules.json`
   - Restart server or call `POST /api/rules/load-defaults`

---

## 📊 Dashboard Features

### 1. Alert Summary Cards
Four cards showing:
- **Total Alerts**: Overall count
- **By Severity**: Critical, Warning, Info breakdown
- **By Status**: Open, Escalated, Auto-Closed, Resolved counts
- **Auto-Closed Today**: Recent auto-closures

### 2. Top Offenders Table
Leaderboard of drivers with most alerts:
- Rank with medals (🥇🥈🥉)
- Open and escalated alert counts
- Total alerts
- Last alert timestamp
- Clickable rows for drill-down

### 3. Trend Chart
Line chart showing:
- Total alerts per day
- Escalated alerts per day
- Auto-closed alerts per day
- Resolved alerts per day
- Time range selector (7d/30d/90d)

### 4. Source Distribution Pie Chart
Shows alert breakdown by type:
- Overspeeding
- Compliance
- Negative Feedback
- Document Expiry
- Safety

### 5. Recent Activities Timeline
Stream of recent alert events:
- Alert created
- Escalated to CRITICAL
- Auto-closed (with reason)
- Manually resolved
- Color-coded by action type

### 6. Auto-Closed Alerts Table
Recently auto-closed alerts with:
- Alert ID
- Source type
- Closed timestamp
- Auto-closure reason
- Time filter (24h/7d/30d)

### 7. Alert Detail Modal
Click any alert to view:
- Full alert information
- Complete metadata
- State transition history timeline
- Resolve button (if not resolved)
- Resolution notes (if resolved)

---

## 🧪 Testing

### Run All Tests
```bash
# Backend unit tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test file
pytest tests/test_rule_engine.py -v
```

### API Testing

#### Quick Test Script
```bash
python scripts/quick_test.py
```

#### Manual Testing
```bash
# Start server
uvicorn app.main:app --reload

# In another terminal
python scripts/test_phase3.py
```

### Test Scenarios

#### Escalation Demo
```python
# Create 3 overspeeding alerts for same driver within 1 hour
# Expected: 3rd alert auto-escalates to CRITICAL

POST /api/alerts (driver: DRV001, speed: 85)  # Alert 1: OPEN
POST /api/alerts (driver: DRV001, speed: 90)  # Alert 2: OPEN
POST /api/alerts (driver: DRV001, speed: 95)  # Alert 3: ESCALATED ✓
```

#### Auto-Close Demo
```python
# Create compliance alert, then mark document valid
# Expected: Alert auto-closes within 5 minutes

POST /api/alerts (source: COMPLIANCE, document_valid: false)  # Status: OPEN
# Wait for background job OR
# Manually update metadata.document_valid = true
# After job runs: Status: AUTO_CLOSED ✓
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000
```

---

## 🚢 Deployment

### Docker Deployment (Recommended)

1. **Build Docker image**
```bash
   docker build -t alert-system:latest .
```

2. **Run with Docker Compose**
```bash
   docker-compose up -d
```

   This starts:
   - FastAPI backend (port 8000)
   - MongoDB (port 27017)
   - React frontend (port 3000)

### Manual Deployment

#### Backend (Production)
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### Frontend (Production)
```bash
cd frontend
npm run build

# Serve with nginx or any static server
# Build output is in frontend/build/
```

### Environment Variables (Production)
```env
# MongoDB
MONGODB_URL=mongodb://production-host:27017
DATABASE_NAME=alert_system_prod

# JWT (Use strong secret!)
SECRET_KEY=<generate-new-key-for-production>
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application
ENVIRONMENT=production
LOG_LEVEL=WARNING
DEBUG=False

# CORS (restrict to your domain)
ALLOWED_ORIGINS=https://yourdomain.com
```

### Monitoring

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (ADMIN only)
- **Logs**: Check application logs for job executions
- **Database**: Monitor MongoDB performance

---

## 🎨 Design Decisions

### 1. MongoDB vs PostgreSQL
**Decision:** MongoDB  
**Rationale:**
- Flexible schema for varied alert metadata
- Powerful aggregation pipeline for dashboard queries
- Horizontal scalability
- JSON-like documents match alert structure

**Trade-off:** Less strict ACID guarantees, but acceptable for this use case

### 2. Real-time vs Batch Processing
**Decision:** Hybrid approach
- **Real-time escalation** on alert creation
- **Batch auto-closure** every 5 minutes

**Rationale:**
- Escalation needs immediate response
- Auto-closure can tolerate slight delay

**Trade-off:** Auto-closure has up to 5-minute latency

### 3. In-Memory vs Database Rules
**Decision:** Hybrid
- Rules loaded from DB at startup
- Cached in memory with TTL

**Rationale:** Balance between performance and persistence

**Trade-off:** Rule changes require cache invalidation

### 4. APScheduler vs Celery
**Decision:** APScheduler  
**Rationale:**
- Lightweight, no additional infrastructure
- Sufficient for 5-minute intervals
- Easier setup and deployment

**Trade-off:** Less scalable than Celery for high-frequency jobs

### 5. JWT vs Session-Based Auth
**Decision:** JWT  
**Rationale:**
- Stateless authentication
- Easier to scale horizontally
- Works well with SPAs

**Trade-off:** Cannot revoke tokens before expiry

---

## ⚡ Performance Optimization

### Database Optimization

#### Indexes
```javascript
// Alerts collection
db.alerts.createIndex({ alert_id: 1 }, { unique: true })
db.alerts.createIndex({ status: 1, timestamp: -1 })
db.alerts.createIndex({ "metadata.driver_id": 1, source_type: 1, timestamp: -1 })

// Rules collection
db.rules.createIndex({ source_type: 1, is_active: 1 })

// Users collection
db.users.createIndex({ username: 1 }, { unique: true })
<img width="760" height="347" alt="Screenshot 2025-11-10 115918" src="https://github.com/user-attachments/assets/95b657bf-5cf2-4938-a1f3-bef5ec883324" />

```
<img width="760" height="347" alt="Screenshot 2025-11-10 115918" src="https://github.com/user-attachments/assets/2e120a30-7e08-4c35-b015-afaacf443319" />

#### Aggregation Pipelines
- Use `$match` early to filter documents
- Use `$project` to limit fields
- Use `$limit` for pagination

### Caching Strategy
- Active rules cached for 5 minutes
- Dashboard aggregations cached for 60 seconds
- Cache invalidation on data updates

### API Response Times
- Alert creation: <100ms
- Dashboard queries: <200ms (with caching)
- Rule evaluation: <50ms per alert
- <img width="1067" height="720" alt="Screenshot 2025-11-10 120254" src="https://github.com/user-attachments/assets/9f32e987-de95-4c58-8c3b-c2682b490fea" />


### Scalability Considerations
- **Horizontal Scaling**: Stateless backend, can run multiple instances
- **Database Sharding**: MongoDB supports sharding by driver_id
- **Load Balancing**: Use nginx or cloud load balancer
- **Background Jobs**: Can be offloaded to separate worker instances

---
<img width="1069" height="705" alt="Screenshot 2025-11-10 115750" src="https://github.com/user-attachments/assets/6f1e609e-8600-4875-8b4d-f9384e300491" />
<img width="1059" height="821" alt="Screenshot 2025-11-10 115805" src="https://github.com/user-attachments/assets/07acb51c-e034-4421-abc5-3d52a465db3e" />
<img width="1051" height="775" alt="Screenshot 2025-11-10 115940" src="https://github.com/user-attachments/assets/452b1af9-ad4b-48e8-be03-f82e32f7f2da" />




## 📊 Complexity Analysis

### Time Complexity

| Operation | Time Complexity | Explanation |
|-----------|----------------|-------------|
| Create Alert | O(1) | Single insert + rule check (indexed query) |
| List Alerts | O(log n) | Indexed query with pagination |
| Rule Evaluation | O(m * log n) | m rules * query alerts in time window |
| Dashboard Summary | O(n) | Aggregation pipeline, optimized with indexes |
| Top Offenders | O(n log n) | Group by driver + sort |
| Background Job | O(k * m) | k alerts to check * m rules per alert |

Where:
- n = total number of alerts
- m = number of rules
- k = number of OPEN/ESCALATED alerts

### Space Complexity

| Component | Space Complexity | Notes |
|-----------|-----------------|-------|
| Alert Storage | O(n) | Linear with number of alerts |
| Rule Cache | O(m) | Constant (limited number of rules) |
| Background Job | O(k) | Alerts loaded in memory during processing |
| Dashboard Aggregations | O(1) | Result set bounded by limit parameters |

### Optimization Strategies
1. **Indexes**: Reduce query time from O(n) to O(log n)
2. **Pagination**: Limit memory usage for large result sets
3. **Aggregation Pipelines**: Single-pass data processing
4. **Caching**: Avoid repeated database queries
5. **Batch Processing**: Process multiple alerts in single job run

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature
