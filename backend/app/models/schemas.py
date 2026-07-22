"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# User Schemas
class UserCreate(BaseModel):
    """Schema for user creation."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    """Schema for login response."""
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


# APIKey Schemas
class APIKeyCreate(BaseModel):
    """Schema for API key creation."""
    name: str = Field(..., min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    id: int
    key: str = Field(..., description="The full API key (only shown on creation)")
    name: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """Schema for API key list response (without full key)."""
    id: int
    key: str = Field(..., description="Masked API key (prefix only)")
    name: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Process Request/Response Schemas
class ProcessRequest(BaseModel):
    """Schema for /process endpoint request."""
    prompt: str = Field(..., min_length=1, description="User prompt to process")
    model: Optional[str] = None  # If None, will use orchestrator to decide


class ProcessResponse(BaseModel):
    """Schema for /process endpoint response."""
    request_id: str
    model_used: str
    prompt: str
    response: str
    execution_time_ms: float
    tools_executed: list[dict] = []  # Changed to list of dicts with action details
    tool_flags: dict[str, list[str]] = {}


# Health Check Schema
class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str
    version: str
    database: str
    ollama: str
    timestamp: datetime
