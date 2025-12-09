"""FastAPI dependencies for Accounts Service."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import Settings, get_settings
from database import get_db

# Use HTTPBearer for simple Bearer token input in Swagger UI
bearer_scheme = HTTPBearer(
    scheme_name="Bearer Token",
    description="Enter your JWT access token from the auth service",
)


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str  # User ID
    type: str  # "access" or "refresh"


class CurrentUser(BaseModel):
    """Represents the current authenticated user."""

    id: str
    is_active: bool = True


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    """
    Dependency to get the current authenticated user from JWT token.

    Validates the JWT token from the auth service.

    Args:
        token: JWT access token from Authorization header
        settings: Application settings

    Returns:
        CurrentUser: The authenticated user info

    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.auth_jwt_secret_key,
            algorithms=[settings.auth_jwt_algorithm],
        )
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if user_id is None:
            raise credentials_exception

        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type: expected 'access', got '{token_type}'",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError as e:
        # Log for debugging - remove in production
        print(f"JWT decode error: {e}")
        print(f"Secret key (first 10 chars): {settings.auth_jwt_secret_key[:10]}...")
        raise credentials_exception

    return CurrentUser(id=user_id)


# Type aliases for cleaner dependency injection
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
DBSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]

