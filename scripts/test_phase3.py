#!/usr/bin/env python3
"""
Phase 3 Testing Script: Background Jobs + Dashboard

This script tests the Phase 3 functionality including:
- Dashboard API endpoints
- Background job system
- Auto-close functionality

Usage:
    python scripts/test_phase3.py
    
    # With custom base URL
    BASE_URL=http://localhost:8000 python scripts/test_phase3.py
"""

import os
import sys
import time
import requests
from datetime import datetime
from typing import Optional

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    class Fore:
        GREEN = '\033[92m'
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        MAGENTA = '\033[95m'
        RESET = '\033[0m'
    
    class Style:
        BRIGHT = '\033[1m'
        RESET_ALL = '\033[0m'
    
    HAS_COLORAMA = False


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "Admin123!"
REQUEST_TIMEOUT = 10


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def print_success(message: str) -> None:
    """Print success message."""
    print(f"{Fore.GREEN}✅ {message}{Fore.RESET}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"{Fore.RED}❌ {message}{Fore.RESET}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"{Fore.CYAN}ℹ️  {message}{Fore.RESET}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"{Fore.YELLOW}⚠️  {message}{Fore.RESET}")


def print_header(message: str) -> None:
    """Print header message."""
    print(f"\n{Style.BRIGHT}{Fore.BLUE}{'='*70}{Fore.RESET}")
    print(f"{Style.BRIGHT}{Fore.BLUE}{message}{Fore.RESET}")
    print(f"{Style.BRIGHT}{Fore.BLUE}{'='*70}{Fore.RESET}\n")


def make_request(
    method: str,
    url: str,
    headers: Optional[dict] = None,
    json_data: Optional[dict] = None,
    data: Optional[dict] = None,
) -> Optional[requests.Response]:
    """Make HTTP request with error handling."""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        elif method.upper() == "POST":
            if json_data:
                response = requests.post(
                    url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT
                )
            else:
                response = requests.post(
                    url, data=data, headers=headers, timeout=REQUEST_TIMEOUT
                )
        else:
            print_error(f"Unsupported method: {method}")
            return None
        
        return response
        
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {BASE_URL}. Is the server running?")
        return None
    except requests.exceptions.Timeout:
        print_error(f"Request to {url} timed out")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return None


# ============================================================================
# TEST FUNCTIONS
# ============================================================================


def test_login() -> Optional[str]:
    """Test login and return JWT token."""
    print_info("Logging in...")
    
    login_url = f"{BASE_URL}/auth/login"
    response = make_request(
        "POST",
        login_url,
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )
    
    if not response:
        return None
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("access_token")
        if token:
            print_success(f"Login successful! Token: {token[:20]}...")
            return token
        else:
            print_error("Login response missing access_token")
            return None
    else:
        print_error(f"Login failed: {response.status_code} - {response.text}")
        return None


def test_dashboard_summary(headers: dict) -> bool:
    """Test dashboard summary endpoint."""
    print_info("Test 1: Dashboard Summary...")
    
    url = f"{BASE_URL}/api/dashboard/summary"
    response = make_request("GET", url, headers=headers)
    
    if not response:
        return False
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Total Alerts: {data.get('total_alerts', 0)}")
        print_info(
            f"   Critical: {data.get('critical_count', 0)}, "
            f"Open: {data.get('open_count', 0)}, "
            f"Escalated: {data.get('escalated_count', 0)}"
        )
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text[:200]}")
        return False


def test_top_offenders(headers: dict) -> bool:
    """Test top offenders endpoint."""
    print_info("Test 2: Top Offenders...")
    
    url = f"{BASE_URL}/api/dashboard/top-offenders?limit=5"
    response = make_request("GET", url, headers=headers)
    
    if not response:
        return False
    
    if response.status_code == 200:
        offenders = response.json()
        print_success(f"Found {len(offenders)} offenders")
        for i, o in enumerate(offenders[:3], 1):
            print_info(
                f"   {i}. {o.get('driver_id', 'N/A')}: "
                f"{o.get('total_alerts', 0)} alerts "
                f"({o.get('escalated_alerts', 0)} escalated)"
            )
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text[:200]}")
        return False


def test_create_compliance_alert(headers: dict) -> Optional[str]:
    """Test creating a compliance alert for auto-close testing."""
    print_info("Test 3: Creating compliance alert for auto-close test...")
    
    alert_data = {
        "source_type": "COMPLIANCE",
        "metadata": {
            "driver_id": "DRV_AUTOCLOSE_TEST",
            "document_type": "license",
            "document_valid": False,
            "expiry_date": "2025-01-01",
        },
    }
    
    url = f"{BASE_URL}/api/alerts"
    response = make_request("POST", url, headers=headers, json_data=alert_data)
    
    if not response:
        return None
    
    if response.status_code == 201:
        alert = response.json()
        alert_id = alert.get("alert_id")
        status = alert.get("status", "N/A")
        print_success(f"Created: {alert_id}, Status: {status}")
        
        print_warning(
            "\n⏳ Note: Auto-close will run in the next scheduled job (every 5 minutes)"
        )
        print_warning(
            "   Check server logs for job execution messages like:"
        )
        print_warning("   - 'Starting auto-close scanner job...'")
        print_warning("   - 'Auto-close job JOB-...: checked X, closed Y'")
        
        return alert_id
    else:
        print_error(f"Failed: {response.status_code} - {response.text[:200]}")
        return None


def test_recent_activities(headers: dict) -> bool:
    """Test recent activities endpoint."""
    print_info("Test 4: Recent Activities...")
    
    url = f"{BASE_URL}/api/dashboard/recent-activities?limit=10"
    response = make_request("GET", url, headers=headers)
    
    if not response:
        return False
    
    if response.status_code == 200:
        activities = response.json()
        print_success(f"Found {len(activities)} recent activities")
        for i, a in enumerate(activities[:3], 1):
            alert_id = a.get("alert_id", "N/A")
            action = a.get("action", "N/A")
            timestamp = a.get("timestamp", "N/A")
            print_info(f"   {i}. {alert_id}: {action} at {timestamp}")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text[:200]}")
        return False


def test_trends(headers: dict) -> bool:
    """Test trends endpoint."""
    print_info("Test 5: Trend Data...")
    
    url = f"{BASE_URL}/api/dashboard/trends?days=7"
    response = make_request("GET", url, headers=headers)
    
    if not response:
        return False
    
    if response.status_code == 200:
        trends = response.json()
        print_success(f"Got {len(trends)} days of trend data")
        if trends:
            latest = trends[-1]
            print_info(
                f"   Latest: {latest.get('date')} - "
                f"Total: {latest.get('total_alerts', 0)}, "
                f"Escalated: {latest.get('escalated', 0)}"
            )
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text[:200]}")
        return False


def test_source_distribution(headers: dict) -> bool:
    """Test source distribution endpoint."""
    print_info("Test 6: Source Distribution...")
    
    url = f"{BASE_URL}/api/dashboard/source-distribution"
    response = make_request("GET", url, headers=headers)
    
    if not response:
        return False
    
    if response.status_code == 200:
        distribution = response.json()
        print_success("Source distribution retrieved")
        for source_type, count in distribution.items():
            print_info(f"   {source_type}: {count}")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text[:200]}")
        return False


def test_auto_closed(headers: dict) -> bool:
    """Test auto-closed alerts endpoint."""
    print_info("Test 7: Auto-Closed Alerts...")
    
    url = f"{BASE_URL}/api/dashboard/auto-closed?hours=24"
    response = make_request("GET", url, headers=headers)
    
    if not response:
        return False
    
    if response.status_code == 200:
        alerts = response.json()
        print_success(f"Found {len(alerts)} auto-closed alerts in last 24 hours")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text[:200]}")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def test_phase3() -> int:
    """
    Main test execution function.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_header("PHASE 3 TESTING: Background Jobs + Dashboard")
    print_info(f"Base URL: {BASE_URL}\n")
    
    # Login
    token = test_login()
    if not token:
        print_error("Login failed. Cannot continue.")
        return 1
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    # Run tests
    results = []
    
    results.append(("Dashboard Summary", test_dashboard_summary(headers)))
    results.append(("Top Offenders", test_top_offenders(headers)))
    results.append(("Create Compliance Alert", test_create_compliance_alert(headers) is not None))
    results.append(("Recent Activities", test_recent_activities(headers)))
    results.append(("Trends", test_trends(headers)))
    results.append(("Source Distribution", test_source_distribution(headers)))
    results.append(("Auto-Closed Alerts", test_auto_closed(headers)))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print_success("\n🎉 All tests passed!")
        print_info("\nVerification Checklist:")
        print_info("  ✅ Dashboard endpoints are working")
        print_info("  ✅ Background scheduler should be running")
        print_info("  ⏰ Check server logs for:")
        print_info("     - '✅ Background scheduler started'")
        print_info("     - Auto-close job executions every 5 minutes")
        print_info("     - 'Auto-close job JOB-...: checked X, closed Y'")
        return 0
    else:
        print_error(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = test_phase3()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_error("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

