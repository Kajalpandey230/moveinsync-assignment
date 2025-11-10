#!/usr/bin/env python3
"""
Interactive script to test a single API endpoint.

This script allows you to quickly test any endpoint with automatic
authentication token inclusion.

Usage:
    # Test GET endpoint
    python scripts/test_single_endpoint.py --endpoint /api/alerts --method GET
    
    # Test POST endpoint with JSON data
    python scripts/test_single_endpoint.py --endpoint /api/alerts --method POST --data '{"source_type":"OVERSPEEDING","metadata":{"driver_id":"DRV001"}}'
    
    # Test with custom base URL
    python scripts/test_single_endpoint.py --endpoint /api/alerts --base-url http://localhost:8000
    
    # Test without authentication
    python scripts/test_single_endpoint.py --endpoint /health --method GET --no-auth
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, Any, Optional

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
        RESET = '\033[0m'
    
    class Style:
        BRIGHT = '\033[1m'
        RESET_ALL = '\033[0m'
    
    HAS_COLORAMA = False


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "Admin123!"
REQUEST_TIMEOUT = 10


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def print_colored(color: str, message: str) -> None:
    """Print colored message."""
    print(f"{color}{message}{Fore.RESET}")


def print_success(message: str) -> None:
    """Print success message."""
    print_colored(Fore.GREEN, f"✅ {message}")


def print_error(message: str) -> None:
    """Print error message."""
    print_colored(Fore.RED, f"❌ {message}")


def print_info(message: str) -> None:
    """Print info message."""
    print_colored(Fore.CYAN, f"ℹ️  {message}")


def print_header(message: str) -> None:
    """Print header message."""
    print(f"\n{Style.BRIGHT}{Fore.BLUE}{'='*60}{Fore.RESET}")
    print(f"{Style.BRIGHT}{Fore.BLUE}{message}{Fore.RESET}")
    print(f"{Style.BRIGHT}{Fore.BLUE}{'='*60}{Fore.RESET}\n")


def get_auth_token(base_url: str, username: str, password: str) -> Optional[str]:
    """
    Get JWT authentication token.
    
    Args:
        base_url: Base URL of the API
        username: Username
        password: Password
        
    Returns:
        JWT token or None if failed
    """
    login_url = f"{base_url}/auth/login"
    
    try:
        response = requests.post(
            login_url,
            data={"username": username, "password": password},
            timeout=REQUEST_TIMEOUT,
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print_error(
                f"Login failed: {response.status_code} - {response.text}"
            )
            return None
            
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {base_url}. Is the server running?")
        return None
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        return None


def make_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    json_data: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    """
    Make HTTP request.
    
    Args:
        method: HTTP method
        url: Request URL
        headers: Request headers
        data: Form data
        json_data: JSON data
        
    Returns:
        Response object
    """
    method_upper = method.upper()
    
    if method_upper == "GET":
        return requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    elif method_upper == "POST":
        if json_data:
            return requests.post(
                url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT
            )
        else:
            return requests.post(
                url, data=data, headers=headers, timeout=REQUEST_TIMEOUT
            )
    elif method_upper == "PUT":
        if json_data:
            return requests.put(
                url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT
            )
        else:
            return requests.put(
                url, data=data, headers=headers, timeout=REQUEST_TIMEOUT
            )
    elif method_upper == "PATCH":
        if json_data:
            return requests.patch(
                url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT
            )
        else:
            return requests.patch(
                url, data=data, headers=headers, timeout=REQUEST_TIMEOUT
            )
    elif method_upper == "DELETE":
        return requests.delete(url, headers=headers, timeout=REQUEST_TIMEOUT)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


def pretty_print_json(data: Any) -> None:
    """
    Pretty print JSON data.
    
    Args:
        data: JSON-serializable data
    """
    try:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Could not pretty print JSON: {str(e)}")
        print(data)


def print_response_details(response: requests.Response) -> None:
    """
    Print detailed response information.
    
    Args:
        response: HTTP response object
    """
    print_header("Response Details")
    
    # Status
    status_color = Fore.GREEN if 200 <= response.status_code < 300 else Fore.RED
    print_colored(
        status_color,
        f"Status: {response.status_code} {response.reason}",
    )
    
    # Headers
    print_info("\nHeaders:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    # Body
    print_info("\nBody:")
    try:
        body = response.json()
        pretty_print_json(body)
    except ValueError:
        # Not JSON, print as text
        print(response.text[:500])  # Limit to 500 chars
        if len(response.text) > 500:
            print("... (truncated)")


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main() -> int:
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Test a single API endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test GET endpoint
  python scripts/test_single_endpoint.py --endpoint /api/alerts --method GET
  
  # Test POST endpoint with JSON
  python scripts/test_single_endpoint.py --endpoint /api/alerts --method POST \\
    --data '{"source_type":"OVERSPEEDING","metadata":{"driver_id":"DRV001"}}'
  
  # Test without authentication
  python scripts/test_single_endpoint.py --endpoint /health --no-auth
        """,
    )
    
    parser.add_argument(
        "--endpoint",
        required=True,
        help="API endpoint path (e.g., /api/alerts)",
    )
    
    parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "POST", "PUT", "PATCH", "DELETE"],
        help="HTTP method (default: GET)",
    )
    
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL (default: {DEFAULT_BASE_URL})",
    )
    
    parser.add_argument(
        "--data",
        help="JSON data for POST/PUT/PATCH requests",
    )
    
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Skip authentication",
    )
    
    parser.add_argument(
        "--username",
        default=DEFAULT_USERNAME,
        help=f"Username for authentication (default: {DEFAULT_USERNAME})",
    )
    
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help=f"Password for authentication (default: {DEFAULT_PASSWORD})",
    )
    
    args = parser.parse_args()
    
    # Build full URL
    endpoint = args.endpoint.lstrip("/")
    base_url = args.base_url.rstrip("/")
    full_url = f"{base_url}/{endpoint}"
    
    print_header("Single Endpoint Test")
    print_info(f"URL: {full_url}")
    print_info(f"Method: {args.method}")
    
    # Get authentication token if needed
    headers = {"Content-Type": "application/json"}
    if not args.no_auth:
        print_info("Authenticating...")
        token = get_auth_token(args.base_url, args.username, args.password)
        if not token:
            print_error("Authentication failed. Use --no-auth to skip.")
            return 1
        headers["Authorization"] = f"Bearer {token}"
        print_success("Authentication successful")
    else:
        print_info("Skipping authentication")
    
    # Parse JSON data if provided
    json_data = None
    if args.data:
        try:
            json_data = json.loads(args.data)
            print_info(f"Request data: {json.dumps(json_data, indent=2)}")
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON data: {str(e)}")
            return 1
    
    # Make request
    print_info(f"\nMaking {args.method} request...")
    try:
        response = make_request(
            args.method, full_url, headers=headers, json_data=json_data
        )
        
        # Print response
        print_response_details(response)
        
        # Exit code based on status
        if 200 <= response.status_code < 300:
            print_success("\n✅ Request successful!")
            return 0
        else:
            print_error(f"\n❌ Request failed with status {response.status_code}")
            return 1
            
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {args.base_url}. Is the server running?")
        return 1
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_error("\nInterrupted by user")
        sys.exit(1)

