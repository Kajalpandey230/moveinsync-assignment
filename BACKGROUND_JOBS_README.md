# Background Job System Documentation

## Overview

This document describes the background job system for auto-closing alerts in the FastAPI Alert Management System.

## Architecture

The system consists of four main components:

1. **Job Service** (`app/services/job_service.py`) - Manages job records in MongoDB
2. **Auto-Close Job** (`app/jobs/auto_close_job.py`) - Implements the auto-closure scanner
3. **Scheduler** (`app/jobs/scheduler.py`) - APScheduler setup and management
4. **Integration** (`app/main.py`) - Lifecycle management

## Components

### 1. Job Service (`app/services/job_service.py`)

Provides functions for managing background job records:

- **`create_job_record(job_type, db)`** - Creates a new job record with status "running"
- **`update_job_record(job_id, stats, status, errors, db)`** - Updates job with completion data
- **`get_recent_jobs(limit, db)`** - Retrieves recent job records

**Job ID Format:** `JOB-{timestamp}-{random_hex}`

**Example:**
```python
job = await create_job_record("auto_close_scanner", db)
# Returns: BackgroundJobModel with job_id="JOB-20250115-143022-a1b2c3d4"
```

### 2. Auto-Close Job (`app/jobs/auto_close_job.py`)

The main scanner function that:

1. Creates a job record at start
2. Calls `rule_engine.evaluate_all_pending_alerts()` to process alerts
3. Updates job record with statistics
4. Handles errors gracefully

**Function:** `auto_close_scanner(db) -> Dict[str, int]`

**Returns:**
```python
{
    "total_checked": 150,
    "auto_closed": 12,
    "alerts_processed": 150,
    "alerts_closed": 12,
    "alerts_escalated": 0
}
```

**Features:**
- Idempotent (safe to run multiple times)
- Continues processing if individual alerts fail
- Comprehensive error logging
- Job record tracking

### 3. Scheduler (`app/jobs/scheduler.py`)

Manages APScheduler instance:

- **`start_scheduler(db)`** - Starts scheduler with auto-close job (runs every 5 minutes)
- **`shutdown_scheduler()`** - Gracefully shuts down scheduler
- **`is_scheduler_running()`** - Check if scheduler is running
- **`get_scheduler_status()`** - Get scheduler status and job information

**Configuration:**
- Interval: 5 minutes
- Max instances: 1 (prevents overlapping executions)
- Coalesce: True (combines multiple pending executions)

### 4. Integration (`app/main.py`)

The scheduler is automatically started when the FastAPI app starts and stopped when it shuts down:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.connect()
    db = Database.get_database()
    start_scheduler(db)  # Start on app startup
    yield
    shutdown_scheduler()  # Stop on app shutdown
    await Database.disconnect()
```

## Database Schema

### Background Jobs Collection

Collection: `background_jobs`

**Schema (BackgroundJobModel):**
```python
{
    "_id": ObjectId,
    "job_id": "JOB-20250115-143022-a1b2c3d4",
    "job_type": "auto_close_scanner",
    "status": "completed" | "failed" | "running",
    "started_at": datetime,
    "completed_at": datetime | None,
    "alerts_processed": 150,
    "alerts_closed": 12,
    "alerts_escalated": 0,
    "errors": [],
    "execution_time_ms": 1234.56
}
```

## Usage

### Automatic Execution

The scheduler automatically runs every 5 minutes when the FastAPI app is running. No manual intervention needed.

### Manual Execution (Testing)

You can manually trigger the auto-close scanner:

```python
from app.jobs.auto_close_job import auto_close_scanner
from src.database.connection import Database

db = Database.get_database()
stats = await auto_close_scanner(db)
print(f"Checked: {stats['total_checked']}, Closed: {stats['auto_closed']}")
```

### Querying Job History

```python
from app.services.job_service import get_recent_jobs
from src.database.connection import Database

db = Database.get_database()
recent_jobs = await get_recent_jobs(limit=10, db=db)

for job in recent_jobs:
    print(f"{job.job_id}: {job.status} - {job.alerts_closed} closed")
```

## Monitoring

### Check Scheduler Status

```python
from app.jobs.scheduler import get_scheduler_status

status = get_scheduler_status()
print(status)
# {
#     "running": True,
#     "jobs": [
#         {
#             "id": "auto_close_scanner",
#             "name": "Auto-close alert scanner",
#             "next_run_time": "2025-01-15T14:35:00"
#         }
#     ]
# }
```

### View Job Logs

Job execution is logged at INFO level:

```
INFO:app.jobs.auto_close_job: Starting auto-close scanner job...
INFO:app.jobs.auto_close_job: Job JOB-20250115-143022-a1b2c3d4 started
INFO:app.services.rule_engine: Evaluating 150 pending alerts for auto-close conditions
INFO:app.jobs.auto_close_job: Auto-close job JOB-20250115-143022-a1b2c3d4: checked 150, closed 12
INFO:app.services.job_service: Updated job record: JOB-20250115-143022-a1b2c3d4 - Status: completed
```

## Error Handling

The system is designed to be resilient:

1. **Individual Alert Failures** - Logged but don't stop the job
2. **Database Errors** - Caught and logged, job marked as "failed"
3. **Scheduler Errors** - Logged, scheduler continues running
4. **Job Record Errors** - Logged but don't fail the actual job execution

## Dependencies

Required package:
- `apscheduler>=3.10.4` - For background task scheduling

Install:
```bash
pip install apscheduler
# Or if using pyproject.toml:
uv sync
```

## Configuration

### Changing the Interval

To change the auto-close scan interval, modify `app/jobs/scheduler.py`:

```python
scheduler.add_job(
    func=lambda: _run_async_job(db),
    trigger=IntervalTrigger(minutes=10),  # Change from 5 to 10 minutes
    ...
)
```

### Disabling the Scheduler

To disable automatic scheduling, comment out the scheduler start in `app/main.py`:

```python
# start_scheduler(db)  # Disabled
```

## Troubleshooting

### Scheduler Not Starting

1. Check logs for errors during startup
2. Verify database connection is established before starting scheduler
3. Check if scheduler is already running: `is_scheduler_running()`

### Jobs Not Executing

1. Verify scheduler is running: `get_scheduler_status()`
2. Check job logs for errors
3. Verify database connection is active
4. Check if `evaluate_all_pending_alerts` is working correctly

### Job Records Not Created

1. Check MongoDB connection
2. Verify `background_jobs` collection exists
3. Check logs for database errors

## Best Practices

1. **Idempotency** - Jobs are designed to be safe to run multiple times
2. **Error Isolation** - Individual alert failures don't stop the entire job
3. **Logging** - All operations are logged at appropriate levels
4. **Resource Management** - Event loops are properly cleaned up
5. **Thread Safety** - Scheduler uses thread-safe operations

## Future Enhancements

Potential improvements:
- Add job retry mechanism for failed jobs
- Add job priority system
- Add job scheduling API endpoints
- Add job monitoring dashboard
- Add job execution metrics and alerting

