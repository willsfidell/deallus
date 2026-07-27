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


# Conversation Schemas
class ConversationCreate(BaseModel):
    """Schema for conversation creation."""
    title: Optional[str] = None


class MessageResponse(BaseModel):
    """Schema for message in conversation."""
    id: str
    conversation_id: str
    role: str
    content: str
    model_used: Optional[str] = None
    token_count: int
    tool_executions: list[dict] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: str
    user_id: int
    title: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    """Schema for detailed conversation response with messages."""
    id: str
    user_id: int
    title: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True


# Process Request/Response Schemas
class ProcessRequest(BaseModel):
    """Schema for /process endpoint request."""
    prompt: str = Field(..., min_length=1, description="User prompt to process")
    model: Optional[str] = None  # Deprecated: use force_model instead
    conversation_id: Optional[str] = None  # Optional: if provided, adds to conversation
    force_model: Optional[str] = Field(
        None,
        description="Force routing to specific model (overrides automatic routing)"
    )


class ProcessResponse(BaseModel):
    """Schema for /process endpoint response."""
    request_id: str
    conversation_id: Optional[str] = None
    model_used: str
    # routing_reason: Optional[str] = None  # Explanation of routing decision
    continuity_applied: bool = False  # Whether continuity bonus was applied
    prompt: str
    response: str
    execution_time_ms: float
    tools_executed: list[dict] = []
    tool_flags: dict[str, list[str]] = {}
    context_used: int = 0  # Number of previous messages used
    total_tokens: Optional[int] = None  # Total context tokens used


# Health Check Schema
class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str
    version: str
    database: str
    ollama: str
    timestamp: datetime
