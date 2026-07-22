"""AIDI application entry point."""

import logging
import sys

import uvicorn

from app.main import create_app
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"DEBUG mode: {settings.DEBUG}")

    # Create app
    app = create_app()

    # Run server
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="debug" if settings.DEBUG else "info",
    )
