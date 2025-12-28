"""Authentication routes and JWT logic for Auth Service."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import Settings
from dependencies import AppSettings, CurrentUser, DBSession, EventPublisher
from models import RefreshToken, User
from schemas import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(user_id: str, settings: Settings) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: The user's ID to encode in the token
        settings: Application settings

    Returns:
        str: Encoded JWT access token
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.auth_access_token_expire_minutes
    )
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        to_encode,
        settings.auth_jwt_secret_key,
        algorithm=settings.auth_jwt_algorithm,
    )


def create_refresh_token(user_id: str, db: Session, settings: Settings) -> str:
    """
    Create a JWT refresh token and store it in the database.

    Args:
        user_id: The user's ID
        db: Database session
        settings: Application settings

    Returns:
        str: Encoded JWT refresh token
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.auth_refresh_token_expire_days
    )
    token_id = str(uuid4())

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": token_id,
        "iat": datetime.now(timezone.utc),
    }

    encoded_token = jwt.encode(
        to_encode,
        settings.auth_jwt_secret_key,
        algorithm=settings.auth_jwt_algorithm,
    )

    # Store refresh token in database
    db_token = RefreshToken(
        id=token_id,
        token=encoded_token,
        user_id=user_id,
        expires_at=expire,
    )
    db.add(db_token)
    db.commit()

    return encoded_token


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: User's username
        password: Plain text password

    Returns:
        User if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: DBSession,
    event_publisher: EventPublisher,
) -> User:
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session
        event_publisher: Auth event publisher

    Returns:
        UserResponse: Created user data
    """
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    existing_username = (
        db.query(User).filter(User.username == user_data.username).first()
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Publish user registered event
    await event_publisher.publish_user_registered(
        user_id=user.id,
        email=user.email,
        username=user.username,
    )

    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: DBSession,
    settings: AppSettings,
    event_publisher: EventPublisher,
) -> Token:
    """
    Authenticate user and return access and refresh tokens.

    Uses OAuth2 password flow for compatibility with OpenAPI spec.

    Args:
        form_data: OAuth2 password request form
        request: FastAPI request for client info
        db: Database session
        settings: Application settings
        event_publisher: Auth event publisher

    Returns:
        Token: Access and refresh tokens
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if not user:
        # Publish login failed event
        await event_publisher.publish_login_failed(
            username=form_data.username,
            reason="invalid_credentials",
            ip_address=client_ip,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        await event_publisher.publish_login_failed(
            username=form_data.username,
            reason="inactive_user",
            ip_address=client_ip,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Publish successful login event
    await event_publisher.publish_user_logged_in(
        user_id=user.id,
        username=user.username,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return Token(
        access_token=create_access_token(user.id, settings),
        refresh_token=create_refresh_token(user.id, db, settings),
    )


@router.post("/login/json", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    request: Request,
    db: DBSession,
    settings: AppSettings,
    event_publisher: EventPublisher,
) -> Token:
    """
    Authenticate user with JSON body and return tokens.

    Alternative to OAuth2 form-based login.

    Args:
        login_data: Login credentials
        request: FastAPI request for client info
        db: Database session
        settings: Application settings
        event_publisher: Auth event publisher

    Returns:
        Token: Access and refresh tokens
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if not user:
        await event_publisher.publish_login_failed(
            username=login_data.username,
            reason="invalid_credentials",
            ip_address=client_ip,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        await event_publisher.publish_login_failed(
            username=login_data.username,
            reason="inactive_user",
            ip_address=client_ip,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    await event_publisher.publish_user_logged_in(
        user_id=user.id,
        username=user.username,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return Token(
        access_token=create_access_token(user.id, settings),
        refresh_token=create_refresh_token(user.id, db, settings),
    )


@router.post("/refresh", response_model=Token)
def refresh_tokens(
    refresh_request: RefreshTokenRequest,
    db: DBSession,
    settings: AppSettings,
) -> Token:
    """
    Refresh access token using a valid refresh token.

    Implements token rotation - old refresh token is revoked.

    Args:
        refresh_request: Refresh token request
        db: Database session
        settings: Application settings

    Returns:
        Token: New access and refresh tokens
    """
    token = refresh_request.refresh_token

    # Find the refresh token in database
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if db_token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    if db_token.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Get the user
    user = db.query(User).filter(User.id == db_token.user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Revoke old refresh token (token rotation)
    db_token.is_revoked = True
    db.commit()

    # Generate new tokens
    return Token(
        access_token=create_access_token(user.id, settings),
        refresh_token=create_refresh_token(user.id, db, settings),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    refresh_request: RefreshTokenRequest,
    db: DBSession,
    current_user: CurrentUser,
    event_publisher: EventPublisher,
) -> MessageResponse:
    """
    Logout user by revoking the refresh token.

    Args:
        refresh_request: Refresh token to revoke
        db: Database session
        current_user: Current authenticated user
        event_publisher: Auth event publisher

    Returns:
        MessageResponse: Logout success message
    """
    # Find and revoke the refresh token
    db_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == refresh_request.refresh_token,
            RefreshToken.user_id == current_user.id,
        )
        .first()
    )

    if db_token:
        db_token.is_revoked = True
        db.commit()

    # Publish logout event
    await event_publisher.publish_user_logged_out(
        user_id=current_user.id,
        logout_all_devices=False,
    )

    return MessageResponse(message="Successfully logged out")


@router.post("/logout/all", response_model=MessageResponse)
async def logout_all(
    db: DBSession,
    current_user: CurrentUser,
    event_publisher: EventPublisher,
) -> MessageResponse:
    """
    Logout user from all devices by revoking all refresh tokens.

    Args:
        db: Database session
        current_user: Current authenticated user
        event_publisher: Auth event publisher

    Returns:
        MessageResponse: Logout success message
    """
    # Revoke all refresh tokens for the user
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False,  # noqa: E712
    ).update({"is_revoked": True})
    db.commit()

    # Publish logout all event
    await event_publisher.publish_user_logged_out(
        user_id=current_user.id,
        logout_all_devices=True,
    )

    return MessageResponse(message="Successfully logged out from all devices")


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: CurrentUser,
) -> User:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user data
    """
    return current_user


