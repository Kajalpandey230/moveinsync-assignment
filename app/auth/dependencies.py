"""FastAPI dependency functions for authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.database.connection import Database
from src.database.models import UserModel, UserRole
from app.auth.jwt_handler import decode_access_token

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    """
    Get the current authenticated user from JWT token.

    Decodes the JWT token, extracts the username, and queries MongoDB
    to retrieve the user information.

    Args:
        token: JWT token string extracted from Authorization header

    Returns:
        UserModel: The authenticated user model

    Raises:
        HTTPException: With 401 status code if:
            - Token is invalid or expired
            - Username is missing from token
            - User is not found in database
    """
    # Decode the JWT token
    try:
        payload = decode_access_token(token)
    except HTTPException:
        # Re-raise HTTPException from decode_access_token
        raise

    # Extract username from token payload
    # Try 'sub' first (standard JWT claim), then 'username'
    username = payload.get("sub") or payload.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing username/subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query MongoDB users collection
    try:
        database = Database.get_database()
        users_collection = database["users"]

        # Find user by username
        user_doc = await users_collection.find_one({"username": username})

        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert MongoDB document to UserModel
        # Pydantic will handle _id -> id conversion via alias
        user = UserModel(**user_doc)

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}",
        )


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """
    Get the current active user.

    Checks if the user account is active before allowing access.

    Args:
        current_user: The current authenticated user from get_current_user

    Returns:
        UserModel: The active user model

    Raises:
        HTTPException: With 400 status code if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return current_user


async def require_admin(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    """
    Require admin role for access.

    Checks if the user has ADMIN role before allowing access.

    Args:
        current_user: The current active user from get_current_active_user

    Returns:
        UserModel: The admin user model

    Raises:
        HTTPException: With 403 status code if user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: Admin role required",
        )
    return current_user


async def require_operator(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    """
    Require operator or admin role for access.

    Checks if the user has OPERATOR or ADMIN role before allowing access.

    Args:
        current_user: The current active user from get_current_active_user

    Returns:
        UserModel: The operator or admin user model

    Raises:
        HTTPException: With 403 status code if user is neither operator nor admin
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: Operator or Admin role required",
        )
    return current_user


async def require_viewer(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    """
    Require any authenticated active user (all roles allowed).

    Any authenticated and active user can access resources protected by this dependency.

    Args:
        current_user: The current active user from get_current_active_user

    Returns:
        UserModel: The authenticated active user model
    """
    return current_user

