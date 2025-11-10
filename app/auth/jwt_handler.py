"""JWT token management for authentication."""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, ExpiredSignatureError, jwt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# JWT configuration
ALGORITHM = "HS256"
DEFAULT_EXPIRATION_HOURS = 24


def get_secret_key() -> str:
    """
    Get JWT secret key from environment variable.

    Returns:
        str: JWT secret key

    Raises:
        ValueError: If SECRET_KEY is not set in environment variables
    """
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError(
            "SECRET_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    return secret_key


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with payload data.

    Args:
        data: Dictionary containing data to encode in the token (e.g., user_id, username)
        expires_delta: Optional timedelta for token expiration.
                      If None, defaults to 24 hours

    Returns:
        str: Encoded JWT token string

    Raises:
        ValueError: If SECRET_KEY is not set in environment variables
    """
    try:
        secret_key = get_secret_key()
    except ValueError as e:
        raise ValueError(str(e))

    # Create a copy of the data to avoid modifying the original
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=DEFAULT_EXPIRATION_HOURS)

    # Add expiration claim
    to_encode.update({"exp": expire})

    # Add subject claim if not already present
    if "sub" not in to_encode:
        # Use a default subject if none provided
        to_encode.update({"sub": str(data.get("user_id", data.get("username", "unknown")))})

    # Encode the token
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: With 401 status code if:
            - Token is expired
            - Token is invalid
            - Token cannot be decoded
            - SECRET_KEY is missing
    """
    try:
        secret_key = get_secret_key()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: SECRET_KEY is not set",
        )

    try:
        # Decode and verify the token
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        # Handle expired tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        # Handle invalid tokens (malformed, invalid signature, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

