"""Authentication utilities for AIDI."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import User, APIKey


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hashlib.sha256(password.encode()).hexdigest() == hashed


def generate_api_key() -> tuple[str, str]:
    """
    Generate an API key and its hash.

    Returns:
        Tuple of (full_key, key_hash) for storage
    """
    # Generate a random key
    full_key = f"aidi_{secrets.token_urlsafe(48)}"

    # Hash the key for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    return full_key, key_hash


def mask_api_key(key: str) -> str:
    """
    Mask an API key for display (show only first and last 4 chars).

    Args:
        key: Full API key or key hash

    Returns:
        Masked key like "aidi_****...****"
    """
    if len(key) <= 16:
        return key

    return f"{key[:8]}...{key[-8:]}"


def verify_api_key(db: Session, api_key: str) -> Optional[User]:
    """
    Verify an API key and return the associated user.

    Args:
        db: Database session
        api_key: Full API key to verify

    Returns:
        User object if valid, None otherwise
    """
    try:
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Look up the API key
        api_key_obj = db.query(APIKey).filter(
            APIKey.key == key_hash,
            APIKey.is_active == True,
        ).first()

        if not api_key_obj:
            return None

        # Check if user is active
        user = db.query(User).filter(
            User.id == api_key_obj.user_id,
            User.is_active == True,
        ).first()

        if not user:
            return None

        # Update last_used_at
        api_key_obj.last_used_at = datetime.utcnow()
        db.commit()

        return user

    except Exception as e:
        return None


def create_user(db: Session, email: str, username: str, password: str) -> Optional[User]:
    """
    Create a new user.

    Args:
        db: Database session
        email: User email
        username: Username
        password: Plain text password (will be hashed)

    Returns:
        Created User object or None if creation failed
    """
    try:
        # Check if email or username already exists
        existing = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing:
            return None

        # Create new user
        hashed_password = hash_password(password)
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    except Exception as e:
        db.rollback()
        return None


def verify_user_credentials(db: Session, email: str, password: str) -> Optional[User]:
    """
    Verify user credentials.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        User object if credentials valid, None otherwise
    """
    try:
        user = db.query(User).filter(User.email == email, User.is_active == True).first()

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    except Exception as e:
        return None


def create_api_key(db: Session, user_id: int, name: str) -> Optional[tuple[str, APIKey]]:
    """
    Create a new API key for a user.

    Args:
        db: Database session
        user_id: User ID
        name: Name for the API key

    Returns:
        Tuple of (full_key, APIKey object) or None if creation failed
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return None

        # Generate key
        full_key, key_hash = generate_api_key()

        # Create API key record
        api_key = APIKey(
            key=key_hash,
            user_id=user_id,
            name=name,
            is_active=True,
        )

        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        return full_key, api_key

    except Exception as e:
        db.rollback()
        return None


def get_user_api_keys(db: Session, user_id: int) -> list[APIKey]:
    """
    Get all API keys for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of APIKey objects
    """
    return db.query(APIKey).filter(APIKey.user_id == user_id).all()
