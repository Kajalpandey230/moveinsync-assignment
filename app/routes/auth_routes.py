"""Authentication routes for user registration, login, and password management."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from src.database.connection import Database
from src.database.models import UserModel, UserRole
from app.auth.password_utils import (
    hash_password,
    verify_password,
    validate_password_strength,
)
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import (
    get_current_active_user,
)

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class UserRegisterRequest(BaseModel):
    """User registration request model."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    role: UserRole = Field(default=UserRole.VIEWER, description="User role")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "username": "operator1",
                "email": "operator@moveinsync.com",
                "password": "SecurePass123",
                "full_name": "John Operator",
                "role": "OPERATOR",
            }
        }


class UserResponse(BaseModel):
    """User response model (excludes sensitive data)."""

    id: Optional[str] = Field(None, description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether the user is active")
    is_verified: bool = Field(..., description="Whether email is verified")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "username": "operator1",
                "email": "operator@moveinsync.com",
                "full_name": "John Operator",
                "role": "OPERATOR",
                "is_active": True,
                "is_verified": False,
                "created_at": "2025-01-09T10:00:00",
            }
        }


class LoginRequest(BaseModel):
    """Login request model (JSON format)."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="User password")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "Admin123!",
            }
        }


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request model."""

    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "old_password": "OldPass123",
                "new_password": "NewSecurePass123",
            }
        }


class MessageResponse(BaseModel):
    """Generic message response model."""

    message: str = Field(..., description="Response message")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {"example": {"message": "Password changed successfully"}}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def user_model_to_response(user: UserModel) -> UserResponse:
    """
    Convert UserModel to UserResponse (excludes hashed_password).

    Args:
        user: UserModel instance

    Returns:
        UserResponse: User response without sensitive data
    """
    return UserResponse(
        id=str(user.id) if user.id else None,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
    )


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new user account. Public endpoint - no authentication required.",
)
async def register(
    user_data: UserRegisterRequest,
):
    """
    Register a new user account.

    Public endpoint - no authentication required. Validates password strength,
    checks for duplicate username/email, and creates the user in MongoDB.

    Args:
        user_data: User registration data

    Returns:
        UserResponse: Created user information (without password)

    Raises:
        HTTPException: 400 if password is weak or username/email exists
    """
    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    # Get database and users collection
    database = Database.get_database()
    users_collection = database["users"]

    # Check if username already exists
    existing_user = await users_collection.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check if email already exists
    existing_email = await users_collection.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user document for MongoDB
    # Let MongoDB generate the _id automatically
    user_dict = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "full_name": user_data.full_name,
        "role": user_data.role.value,  # Convert enum to string
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow(),
        "updated_at": None,
        "last_login": None,
    }

    # Insert into MongoDB
    result = await users_collection.insert_one(user_dict)

    # Fetch the created user
    created_user_doc = await users_collection.find_one({"_id": result.inserted_id})
    created_user = UserModel(**created_user_doc)

    # Return user response (exclude password)
    return user_model_to_response(created_user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user and return JWT access token. Accepts JSON format.",
)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return JWT access token.

    Args:
        login_data: Login credentials (username and password) in JSON format

    Returns:
        TokenResponse: JWT access token and token type

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Get database and users collection
    database = Database.get_database()
    users_collection = database["users"]

    # Find user by username
    user_doc = await users_collection.find_one({"username": login_data.username})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convert to UserModel
    user = UserModel(**user_doc)

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login timestamp
    await users_collection.update_one(
        {"username": login_data.username},
        {"$set": {"last_login": datetime.utcnow()}},
    )

    # Create access token
    token_data = {
        "sub": user.username,
        "username": user.username,
        "user_id": str(user.id) if user.id else None,
    }
    access_token = create_access_token(data=token_data)

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get details of the currently authenticated user",
)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current active user (from dependency)

    Returns:
        UserResponse: Current user information (without password)
    """
    return user_model_to_response(current_user)


@router.put(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change the password for the current user",
)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Change password for the current user.

    Args:
        password_data: Old and new password
        current_user: Current active user (from dependency)

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: 400 if old password is incorrect or new password is weak
    """
    # Get database and users collection
    database = Database.get_database()
    users_collection = database["users"]

    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password",
        )

    # Validate new password strength
    is_valid, error_message = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    # Hash new password
    new_hashed_password = hash_password(password_data.new_password)

    # Update password in MongoDB
    await users_collection.update_one(
        {"username": current_user.username},
        {
            "$set": {
                "hashed_password": new_hashed_password,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    return MessageResponse(message="Password changed successfully")

