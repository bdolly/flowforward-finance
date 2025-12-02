"""Pydantic schemas for Auth Service request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- User Schemas ---


class UserBase(BaseModel):
    """Base schema for User."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class UserInDB(UserResponse):
    """Schema for user in database (includes hashed password)."""

    hashed_password: str


# --- Authentication Schemas ---


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str  # User ID
    exp: datetime
    type: str  # "access" or "refresh"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str
    password: str


# --- Response Schemas ---


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    service: str
    version: str

