# Troubleshooting Guide - API Testing Issues

## Issue: Escalation Test Failing

### Problem Description
When running `python scripts/quick_test.py`, you see:
```
[Step 1] Testing login...
✅ Login successful! Token: eyJhbGciOiJIUzI1NiIs...

[Step 2] Loading default rules...
⚠️  Load rules failed, but continuing...

[Step 3] Testing escalation scenario...
ℹ️  Creating 3 alerts for driver DRV001
❌ Escalation test failed.
```

### Root Causes

#### 1. **Routes Not Registered in main.py** ✅ FIXED
**Problem:** The `app/main.py` file was only registering `auth_routes`, but not `alert_routes` and `rule_routes`.

**Solution:** Updated `app/main.py` to include all routes:
```python
from app.routes import auth_routes, alert_routes, rule_routes

# Include routes
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(alert_routes.router, tags=["Alerts"])
app.include_router(rule_routes.router, tags=["Rules"])
```

**Action Required:** 
- ✅ Already fixed in `app/main.py`
- **Restart your FastAPI server** for changes to take effect

#### 2. **Port Mismatch**
**Problem:** `app/main.py` runs on port 6000, but test scripts default to port 8000.

**Solution Options:**

**Option A:** Change server port to 8000 (recommended)
```python
# In app/main.py, line 78
uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
```

**Option B:** Use environment variable when running tests
```bash
# Windows PowerShell
$env:BASE_URL="http://localhost:6000"; python scripts/quick_test.py

# Windows CMD
set BASE_URL=http://localhost:6000 && python scripts/quick_test.py

# Linux/Mac
BASE_URL=http://localhost:6000 python scripts/quick_test.py
```

#### 3. **Server Not Running**
**Problem:** FastAPI server is not running or crashed.

**Solution:**
```bash
# Make sure your server is running
# If using uvicorn directly:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Or if running from main.py:
python -m app.main
```

#### 4. **Database Connection Issues**
**Problem:** MongoDB is not running or connection string is incorrect.

**Solution:**
- Check MongoDB is running: `mongosh` or check MongoDB service
- Verify `.env` file has correct `MONGODB_URI`
- Test connection: `curl http://localhost:8000/health`

### Step-by-Step Fix

1. **Verify routes are registered:**
   ```bash
   # Check app/main.py includes all routes
   grep "include_router" app/main.py
   ```
   Should show:
   - `app.include_router(auth_routes.router, ...)`
   - `app.include_router(alert_routes.router, ...)`
   - `app.include_router(rule_routes.router, ...)`

2. **Restart FastAPI server:**
   ```bash
   # Stop current server (Ctrl+C)
   # Then restart:
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. **Verify server is accessible:**
   ```bash
   # Test health endpoint
   curl http://localhost:8000/health
   
   # Or in PowerShell:
   Invoke-WebRequest -Uri http://localhost:8000/health
   ```

4. **Run tests again:**
   ```bash
   python scripts/quick_test.py
   ```

### Expected Output After Fix

```
============================================================
FastAPI Alert Management System - Quick Test
============================================================

ℹ️  Base URL: http://localhost:8000
ℹ️  Testing Phase 2: Alert System + Rule Engine

[Step 1] Testing login...
✅ Login successful! Token: eyJhbGciOiJIUzI1NiIs...

[Step 2] Loading default rules...
✅ Loaded 5 default rules

[Step 3] Testing escalation scenario...
ℹ️  Creating 3 alerts for driver DRV001
✅ Alert 1 created: ALT-2024-... (Status: OPEN)
✅ Alert 2 created: ALT-2024-... (Status: OPEN)
✅ Alert 3 created: ALT-2024-... (Status: OPEN)
ℹ️  Waiting for rule engine to process escalation...

[Step 4] Checking escalation status...
ℹ️  Alert ALT-2024-...: Status=ESCALATED, Severity=CRITICAL
✅ 🚨 ESCALATION SUCCESSFUL! Alert escalated to CRITICAL

[Step 5] Testing dashboard endpoints...
✅ Dashboard summary retrieved:
  Total: 3, Open: 2, Escalated: 1, Critical: 1
✅ Top offenders retrieved: 1 drivers

============================================================
Test Summary
============================================================
✅ All critical tests completed!
```

### Common Error Messages

#### "Could not connect to http://localhost:8000"
- **Cause:** Server not running
- **Fix:** Start FastAPI server

#### "404 Not Found" on `/api/alerts`
- **Cause:** Routes not registered
- **Fix:** Check `app/main.py` includes `alert_routes.router`

#### "401 Unauthorized"
- **Cause:** Invalid credentials or token expired
- **Fix:** Check username/password in test scripts match your admin user

#### "500 Internal Server Error"
- **Cause:** Database connection issue or server error
- **Fix:** Check MongoDB is running, check server logs

### Debugging Tips

1. **Enable verbose logging:**
   ```python
   # In app/main.py, add logging
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Test endpoints manually:**
   ```bash
   # Use the test_single_endpoint.py script
   python scripts/test_single_endpoint.py --endpoint /api/alerts --method GET
   ```

3. **Check FastAPI docs:**
   ```bash
   # Open in browser
   http://localhost:8000/docs
   ```
   This shows all registered endpoints.

4. **Check server logs:**
   - Look at terminal where server is running
   - Check for import errors, route registration errors

### Verification Checklist

- [ ] FastAPI server is running
- [ ] Server is on correct port (8000 or 6000)
- [ ] MongoDB is running and accessible
- [ ] `app/main.py` includes all three route modules
- [ ] Routes are registered with `app.include_router()`
- [ ] Server was restarted after changes
- [ ] Admin user exists with credentials: `admin` / `Admin123!`
- [ ] Test script uses correct BASE_URL

### Still Having Issues?

1. Check server logs for detailed error messages
2. Verify all dependencies are installed: `pip install -r requirements-test.txt`
3. Test individual endpoints using `test_single_endpoint.py`
4. Check FastAPI docs at `http://localhost:8000/docs` to see registered routes

