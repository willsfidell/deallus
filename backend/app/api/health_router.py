"""Health check API endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthCheck

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """
    Health check endpoint.

    Returns:
        Health status of the application
    """
    return HealthCheck(
        status="healthy",
        version=settings.APP_VERSION,
        database="connected",  # TODO: Add actual database check
        ollama="available",  # TODO: Add actual Ollama check
        timestamp=datetime.utcnow(),
    )
