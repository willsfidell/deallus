"""Authentication API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import (
    create_user,
    verify_user_credentials,
    create_api_key,
    get_user_api_keys,
    mask_api_key,
)
from app.models.schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    UserLoginResponse,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user response
    """
    # Create user
    user = create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already exists",
        )

    logger.info(f"New user registered: {user.email}")
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserLoginResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> UserLoginResponse:
    """
    Login user and receive access token.

    Args:
        credentials: Login credentials
        db: Database session

    Returns:
        User info and access token
    """
    # Verify credentials
    user = verify_user_credentials(
        db=db,
        email=credentials.email,
        password=credentials.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # For now, generate a simple token (placeholder)
    # In production, this should be a JWT
    access_token = f"token_{user.id}_{user.username}"

    logger.info(f"User logged in: {user.email}")

    return UserLoginResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/keys", response_model=APIKeyResponse)
async def create_key(
    key_data: APIKeyCreate,
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> APIKeyResponse:
    """
    Create a new API key.

    Args:
        key_data: API key creation data
        credentials: User credentials for verification
        db: Database session

    Returns:
        Created API key response
    """
    # Verify user credentials
    user = verify_user_credentials(
        db=db,
        email=credentials.email,
        password=credentials.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Create API key
    result = create_api_key(
        db=db,
        user_id=user.id,
        name=key_data.name,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create API key",
        )

    full_key, api_key_obj = result

    logger.info(f"API key created for user {user.email}: {key_data.name}")

    # Return with full key (only shown once)
    response = APIKeyResponse.model_validate(api_key_obj)
    response.key = full_key  # Override with full key

    return response


@router.get("/keys", response_model=list[APIKeyListResponse])
async def list_keys(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> list[APIKeyListResponse]:
    """
    List all API keys for a user.

    Args:
        credentials: User credentials
        db: Database session

    Returns:
        List of API keys (masked)
    """
    # Verify user credentials
    user = verify_user_credentials(
        db=db,
        email=credentials.email,
        password=credentials.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Get API keys
    api_keys = get_user_api_keys(db=db, user_id=user.id)

    # Mask the keys for display
    result = []
    for key in api_keys:
        key_response = APIKeyListResponse.model_validate(key)
        key_response.key = mask_api_key(key.key)
        result.append(key_response)

    return result
