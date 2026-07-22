"""Process API endpoints."""

import asyncio
import logging
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import verify_api_key
from app.models.schemas import ProcessRequest, ProcessResponse
from app.tools.registry import tool_registry
from app.services import get_llm_service, LLMError

logger = logging.getLogger(__name__)
router = APIRouter()


async def verify_api_key_header(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    """Dependency to verify API key from header."""
    user = verify_api_key(db=db, api_key=x_api_key)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return user


@router.post("", response_model=ProcessResponse)
async def process(
    request: ProcessRequest,
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
) -> ProcessResponse:
    """
    Process a prompt using AIDI.

    This endpoint:
    1. Runs pre-prompt tools (PII redaction, etc.)
    2. Routes prompt to appropriate model
    3. Generates response
    4. Runs post-result tools (slop detection, etc.)
    5. Returns result

    Args:
        request: Process request with prompt
        user: Authenticated user (from API key verification)
        db: Database session

    Returns:
        Process response with result and metadata
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # Step 1: Run pre-prompt tools
        logger.info(f"[{request_id}] Processing prompt from user {user.email}")
        logger.info(f"[{request_id}] Running pre-prompt tools")

        # Initialize state
        tool_state = {
            "user_id": user.id,
            "user_email": user.email,
            "request_id": request_id,
            "original_prompt": request.prompt,
        }

        # Run pre-prompt tools
        modified_prompt = request.prompt
        tools_executed = []

        try:
            result = await tool_registry.execute_chain(
                "pre_prompt",
                content=modified_prompt,
                initial_state=tool_state,
                metadata={},
            )
            modified_prompt = result.modified_content
            tools_executed = result.state.get("executed_tools", [])
            tool_state = result.state

            logger.info(f"[{request_id}] Pre-prompt tools completed: {tools_executed}")

        except Exception as e:
            logger.error(f"[{request_id}] Pre-prompt tool error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tool execution error: {str(e)}",
            )

        # Step 2: Route to model
        logger.info(f"[{request_id}] Routing prompt to model")

        # Import orchestrator at runtime to ensure it's initialized
        from app.main import orchestrator

        if orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Orchestrator not initialized",
            )

        # Use orchestrator to determine model
        orchestration_result = await orchestrator.route(modified_prompt)
        model_to_use = orchestration_result.model

        logger.info(
            f"[{request_id}] Routed to model: {model_to_use} "
            f"(confidence: {orchestration_result.confidence:.2f})"
        )

        # Step 3: Generate response using LLM
        logger.info(f"[{request_id}] Calling model: {model_to_use}")

        try:
            llm_service = get_llm_service()
            llm_response = await llm_service.generate(
                prompt=modified_prompt,
                model=model_to_use,
                max_tokens=500,
                temperature=0.7,
            )
            logger.info(f"[{request_id}] Model response received ({len(llm_response)} chars)")

        except LLMError as e:
            logger.error(f"[{request_id}] LLM generation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM service error: {str(e)}",
            )

        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error calling LLM: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service unavailable",
            )

        # Step 4: Run post-result tools
        logger.info(f"[{request_id}] Running post-result tools")

        try:
            result = await tool_registry.execute_chain(
                "post_result",
                content=llm_response,
                initial_state=tool_state,
                metadata={},
            )
            final_response = result.modified_content
            executed_post = result.state.get("executed_tools", [])
            tools_executed.extend(executed_post)
            tool_state = result.state

            logger.info(
                f"[{request_id}] Post-result tools completed: {executed_post}"
            )

        except Exception as e:
            logger.error(f"[{request_id}] Post-result tool error: {e}")
            # Don't fail the request on post-result tool error
            final_response = llm_response

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"[{request_id}] Request completed in {execution_time_ms:.2f}ms"
        )

        # Return response
        return ProcessResponse(
            request_id=request_id,
            model_used=model_to_use,
            prompt=request.prompt,
            response=final_response,
            execution_time_ms=execution_time_ms,
            tools_executed=tools_executed,
            tool_flags=tool_state.get("tool_flags", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/health")
async def process_health():
    """
    Health check for process service.

    Returns:
        Status of process service
    """
    return {
        "status": "healthy",
        "tools_loaded": len(tool_registry.pre_prompt_tools) + len(tool_registry.post_result_tools),
        "pre_prompt_tools": [t.name for t in tool_registry.pre_prompt_tools],
        "post_result_tools": [t.name for t in tool_registry.post_result_tools],
    }
