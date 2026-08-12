"""Process API endpoints."""

import asyncio
import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from app.config import settings
from app.db import get_db
from app.auth import verify_api_key
from app.models.schemas import ProcessRequest, ProcessResponse
from app.tools.registry import tool_registry
from app.services import get_llm_service, LLMError, ContextManager, RedisService
from app.services.conversation_service import ConversationService
from app.db.models import Message, Attachment

logger = logging.getLogger(__name__)
router = APIRouter()


async def _generate_and_update_title_task(
    conversation_id: str,
    message_content: str,
    db_url: str,
):
    """
    Background task to generate and update conversation title.

    Args:
        conversation_id: Conversation ID
        message_content: First user message content
        db_url: Database URL for creating new session
    """
    from sqlalchemy.orm import sessionmaker

    try:
        # Create new DB session (can't reuse request session in async task)
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # Get services
            llm_service = get_llm_service()
            redis_service = await RedisService.get_instance()
            conversation_service = ConversationService(redis_service)

            # Generate title
            title = await conversation_service.generate_conversation_title(
                message_content, llm_service
            )

            # Update conversation
            success = conversation_service._update_conversation_title_internal(
                conversation_id, title, db
            )

            if success:
                logger.info(
                    f"[Background] Title generated for {conversation_id}: '{title}'"
                )
            else:
                logger.warning(
                    f"[Background] Failed to update title for {conversation_id}"
                )

        finally:
            db.close()

    except Exception as e:
        logger.error(
            f"[Background] Title generation task failed: {e}", exc_info=True
        )


async def verify_api_key_header(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    """Dependency to verify API key from header."""
    logger.info(f"[verify_api_key_header] Received X-API-Key header. Key starts with: {x_api_key[:20] if x_api_key else 'NONE'}...")
    user = verify_api_key(db=db, api_key=x_api_key)

    if not user:
        logger.error("[verify_api_key_header] API key verification failed. Raising 401 HTTPException")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    logger.info(f"[verify_api_key_header] API key verified successfully for user {user.username}")
    return user


@router.post("", response_model=ProcessResponse)
async def process(
    request: ProcessRequest,
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
) -> ProcessResponse:
    """
    Process a prompt using Deallus orchestrator.

    This endpoint:
    1. Creates or loads conversation context (if conversation_id provided)
    2. Runs pre-prompt tools (PII redaction, etc.)
    3. Routes prompt to appropriate model (with continuity bonus if in conversation)
    4. Generates response using context if available
    5. Runs post-result tools (slop detection, etc.)
    6. Stores messages in conversation if provided
    7. Returns result with metadata

    Args:
        request: Process request with prompt, optional conversation_id, optional force_model
        user: Authenticated user (from API key verification)
        db: Database session

    Returns:
        Process response with result, conversation metadata, and routing explanation
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    conversation_id = request.conversation_id
    routing_reason = None
    continuity_applied = False
    context_used = 0
    total_tokens = 0

    try:
        # Initialize services
        redis_service = await RedisService.get_instance()
        context_manager = ContextManager(redis_service)
        conversation_service = ConversationService(redis_service)

        # Step 0: Handle conversation context
        context_data = {}  # Initialize for all branches
        if conversation_id:
            # Validate that conversation belongs to user
            conversation = conversation_service.get_conversation(
                conversation_id, user.id, db
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Conversation not found or not owned by user",
                )

            logger.info(
                f"[{request_id}] Loading conversation context: {conversation_id}"
            )

            # Load context
            context_data = await context_manager.get_conversation_context(
                conversation_id, db
            )
            context_used = context_data.get("message_count", 0)
            total_tokens = context_data.get("total_tokens", 0)
            previous_model = context_data.get("last_model_used")

            logger.info(
                f"[{request_id}] Conversation context: "
                f"{context_used} messages, {total_tokens} tokens, "
                f"previous_model={previous_model}"
             )
        else:
            previous_model = None
            context_used = 0
            total_tokens = 0
            # Create new conversation
            conversation = conversation_service.create_conversation(
                user_id=user.id, db=db
            )
            conversation_id = conversation.id
            logger.info(f"[{request_id}] Created new conversation: {conversation_id}")

        # Step 0.5: Check if summarization needed
        if (settings.SUMMARIZATION_ENABLED and 
            context_used > 0 and 
            total_tokens > settings.CONTEXT_MAX_TOKENS * settings.SUMMARIZATION_THRESHOLD):
            
            logger.info(
                f"[{request_id}] Token threshold exceeded "
                f"({total_tokens} > {settings.CONTEXT_MAX_TOKENS * settings.SUMMARIZATION_THRESHOLD}). "
                f"Triggering summarization..."
            )
            
            try:
                summary = await context_manager.summarize_old_messages(
                    conversation_id, db
                )
                
                if summary:
                    logger.info(f"[{request_id}] Summarization complete. Reloading context...")
                    # Reload context after summarization
                    context_data = await context_manager.get_conversation_context(
                        conversation_id, db
                    )
                    context_used = context_data.get("message_count", 0)
                    total_tokens = context_data.get("total_tokens", 0)
                    previous_model = context_data.get("last_model_used")
                    
                    logger.info(
                        f"[{request_id}] Context after summarization: "
                        f"{context_used} messages, {total_tokens} tokens"
                    )
            except Exception as e:
                logger.warning(
                    f"[{request_id}] Summarization failed: {e}. Continuing without summarization..."
                )

        # Load attachments if provided
        attachment_texts = []
        if request.attachment_ids:
            logger.info(f"[{request_id}] Loading {len(request.attachment_ids)} attachments")
            
            for att_id in request.attachment_ids:
                attachment = db.query(Attachment).filter(
                    Attachment.id == att_id,
                    Attachment.user_id == user.id
                ).first()
                
                if not attachment:
                    logger.warning(f"[{request_id}] Attachment not found: {att_id}")
                    continue
                
                if attachment.extraction_status != "completed":
                    logger.warning(f"[{request_id}] Attachment not ready: {att_id}")
                    continue
                
                attachment_texts.append({
                    "id": attachment.id,
                    "filename": attachment.filename,
                    "text": attachment.extracted_text,
                    "word_count": attachment.word_count,
                })
        else:
            attachment_texts = []

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

        # Build enhanced prompt with attachments
        enhanced_prompt = modified_prompt
        if attachment_texts:
            prompt_parts = []
            
            for att in attachment_texts:
                # Truncate if needed
                text = att["text"]
                if len(text.split()) > settings.MAX_ATTACHMENT_WORDS_IN_PROMPT:
                    truncated = " ".join(text.split()[:settings.MAX_ATTACHMENT_WORDS_IN_PROMPT])
                    text = truncated + f"\n[... {att['word_count'] - settings.MAX_ATTACHMENT_WORDS_IN_PROMPT} words omitted]"
                
                prompt_parts.append(f"[File: {att['filename']}]\n{text}")
            
            enhanced_prompt = "\n\n".join(prompt_parts) + "\n\nUser question: " + modified_prompt
            logger.info(f"[{request_id}] Enhanced prompt with {len(attachment_texts)} attachments")
        else:
            enhanced_prompt = modified_prompt

        # Step 2: Route to model (with contextual routing if previous_model exists)
        logger.info(f"[{request_id}] Routing prompt to model")

        # Import orchestrator at runtime to ensure it's initialized
        from app.main import orchestrator

        if orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Orchestrator not initialized",
            )

        # Check for forced model first
        if request.force_model:
            model_to_use = request.force_model
            routing_reason = "User specified model"
            logger.info(f"[{request_id}] Using forced model: {model_to_use}")
        else:
            # Use orchestrator with previous model context for continuity
            orchestration_result = await orchestrator.route(
                modified_prompt,
                previous_model=previous_model,
            )
            model_to_use = orchestration_result.model
            routing_reason = orchestration_result.reasoning
            continuity_applied = (
                previous_model is not None
                and "[Continuing]" in orchestration_result.reasoning
            )

            logger.info(
                f"[{request_id}] Routed to model: {model_to_use} "
                f"(confidence: {orchestration_result.confidence:.2f}, "
                f"continuity: {continuity_applied})"
            )

        # Step 3: Generate response using LLM
        logger.info(f"[{request_id}] Calling model: {model_to_use}")

        # Extract conversation history if available
        conversation_messages = None
        if context_used > 0:
            conversation_messages = context_data.get("messages", [])
            logger.info(
                f"[{request_id}] Passing {len(conversation_messages)} context messages to LLM"
            )

        try:
            llm_service = get_llm_service()
            llm_response = await llm_service.generate(
                prompt=enhanced_prompt,
                model=model_to_use,
                max_tokens=500,
                temperature=0.7,
                conversation_messages=conversation_messages,
            )
            logger.info(
                f"[{request_id}] Model response received ({len(llm_response)} chars)"
            )

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

        # Step 5: Store messages in conversation
        logger.info(f"[{request_id}] Storing messages in conversation")

        try:
            # Prepare attachment data for storage
            message_attachments = []
            for att_id in (request.attachment_ids or []):
                attachment = db.query(Attachment).filter(
                    Attachment.id == att_id,
                    Attachment.user_id == user.id
                ).first()
                
                if attachment and attachment.extraction_status == "completed":
                    message_attachments.append({
                        "id": attachment.id,
                        "filename": attachment.filename,
                        "mime_type": attachment.mime_type,
                        "size_bytes": attachment.size_bytes,
                        "extracted_text": attachment.extracted_text,
                        "page_count": attachment.page_count,
                        "word_count": attachment.word_count,
                        "extraction_method": attachment.extraction_method,
                        "ocr_applied": attachment.ocr_applied,
                    })

            # Store user message
            user_token_count = context_manager.estimate_tokens(modified_prompt)
            conversation_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content=request.prompt,  # Store original prompt
                db=db,
                token_count=user_token_count,
                tool_executions=tools_executed,
                attachments=message_attachments,
            )

            # Check if this is the first user message -> trigger title generation
            if settings.TITLE_GENERATION_ENABLED:
                # Count existing messages (just added user message, so count = 1 means it's first)
                message_count = db.query(Message).filter(
                    Message.conversation_id == conversation_id
                ).count()

                if message_count == 1:
                    # First message! Generate title in background
                    logger.info(
                        f"[{request_id}] First message detected, triggering title generation"
                    )
                    asyncio.create_task(
                        _generate_and_update_title_task(
                            conversation_id=conversation_id,
                            message_content=request.prompt,
                            db_url=settings.DATABASE_URL,
                        )
                    )

            # Store assistant message
            assistant_token_count = context_manager.estimate_tokens(final_response)
            conversation_service.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_response,
                db=db,
                model_used=model_to_use,
                token_count=assistant_token_count,
                tool_executions=[],
            )

            logger.info(f"[{request_id}] Messages stored in conversation")

            # Cleanup temporary attachment records
            if request.attachment_ids:
                for att_id in request.attachment_ids:
                    attachment = db.query(Attachment).filter(
                        Attachment.id == att_id
                    ).first()
                    
                    if attachment:
                        db.delete(attachment)
                
                db.commit()
                logger.info(f"[{request_id}] Cleaned up {len(request.attachment_ids)} temporary attachments")

        except Exception as e:
            logger.error(f"[{request_id}] Error storing conversation messages: {e}")
            # Don't fail the request if message storage fails

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"[{request_id}] Request completed in {execution_time_ms:.2f}ms"
        )

        # Return response
        return ProcessResponse(
            request_id=request_id,
            conversation_id=conversation_id,
            model_used=model_to_use,
            routing_reason=routing_reason,
            continuity_applied=continuity_applied,
            prompt=request.prompt,
            response=final_response,
            execution_time_ms=execution_time_ms,
            tools_executed=tools_executed,
            tool_flags=tool_state.get("tool_flags", {}),
            context_used=context_used,
            total_tokens=total_tokens if total_tokens > 0 else None,
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
