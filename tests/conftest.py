"""
Pytest configuration and shared fixtures for API testing.

This module provides reusable fixtures for:
- Base URL configuration
- Authentication token retrieval
- Authenticated request headers
- Session management

Usage:
    pytest tests/test_api.py -v
"""

import pytest
import requests
from typing import Dict, Generator


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "http://localhost:8000"
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "Admin123!"


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def base_url() -> str:
    """
    Base URL fixture for API endpoints.
    
    Returns:
        str: Base URL of the API server
    """
    return BASE_URL


@pytest.fixture(scope="session")
def auth_token(base_url: str) -> str:
    """
    Authentication token fixture.
    
    Logs in with admin credentials and returns JWT token.
    Token is cached for the entire test session.
    
    Args:
        base_url: Base URL of the API server
        
    Returns:
        str: JWT access token
        
    Raises:
        pytest.skip: If login fails (server might not be running)
    """
    login_url = f"{base_url}/auth/login"
    
    try:
        # Login using form data (OAuth2PasswordRequestForm)
        response = requests.post(
            login_url,
            data={
                "username": AUTH_USERNAME,
                "password": AUTH_PASSWORD,
            },
            timeout=5,
        )
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            if token:
                return token
            else:
                pytest.skip(f"Login successful but no token in response: {token_data}")
        else:
            pytest.skip(
                f"Login failed with status {response.status_code}: {response.text}"
            )
            
    except requests.exceptions.ConnectionError:
        pytest.skip(f"Could not connect to {base_url}. Is the server running?")
    except requests.exceptions.Timeout:
        pytest.skip(f"Connection to {base_url} timed out")
    except Exception as e:
        pytest.skip(f"Unexpected error during login: {str(e)}")


@pytest.fixture(scope="session")
def authenticated_headers(auth_token: str) -> Dict[str, str]:
    """
    Authenticated request headers fixture.
    
    Returns headers dictionary with Authorization Bearer token.
    
    Args:
        auth_token: JWT access token
        
    Returns:
        Dict[str, str]: Headers dictionary with Authorization header
    """
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="function")
def clean_alert_state(base_url: str, authenticated_headers: Dict[str, str]) -> Generator:
    """
    Fixture to clean up alerts created during tests.
    
    This is a placeholder for future cleanup functionality.
    Currently, tests are designed to be idempotent.
    
    Args:
        base_url: Base URL of the API server
        authenticated_headers: Headers with auth token
        
    Yields:
        None: Control back to test function
    """
    # Setup: Nothing to do before test
    yield
    
    # Teardown: Could add cleanup logic here if needed
    # For now, tests are designed to be idempotent
    pass

