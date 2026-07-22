"""AIDI FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.orchestrator import HybridOrchestrator
from app.orchestrator.model_registry import model_registry

logger = logging.getLogger(__name__)


# Global orchestrator instance
orchestrator: HybridOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Discover and load model definitions
    try:
        model_registry.discover_models()
        logger.info(f"Model definitions loaded: {len(model_registry.models)} models registered")
    except Exception as e:
        logger.error(f"Failed to discover model definitions: {e}")

    # Discover and load tools
    try:
        from app.tools.registry import tool_registry
        tool_registry.discover_tools()
        logger.info(f"Tools loaded: {len(tool_registry.pre_prompt_tools)} pre-prompt, {len(tool_registry.post_result_tools)} post-result")
    except Exception as e:
        logger.error(f"Failed to load tools: {e}")

    # Initialize orchestrator
    global orchestrator
    orchestrator = HybridOrchestrator(
        text_model=settings.TEXT_MODEL,
        classifier_model=settings.CLASSIFIER_MODEL,
        rule_confidence_threshold=settings.RULE_CONFIDENCE_THRESHOLD,
        llm_confidence_threshold=settings.LLM_CONFIDENCE_THRESHOLD,
    )
    # Inject the discovered models into the orchestrator
    orchestrator.model_registry = model_registry
    logger.info("Orchestrator initialized")

    yield

    # Shutdown
    logger.info("Shutting down AIDI")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI Orchestrator for Distributed Inference",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and register routers
    from app.api import health_router, auth_router, process_router

    app.include_router(health_router.router, prefix="/api/health", tags=["health"])
    app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
    app.include_router(process_router.router, prefix="/api/process", tags=["process"])

    return app
