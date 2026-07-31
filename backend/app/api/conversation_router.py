"""Conversation API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import verify_api_key
from app.db.models import Message, Conversation
from app.models.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    MessageResponse,
)
from app.services.conversation_service import ConversationService
from app.services.redis_service import RedisService, get_conversation_cache_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


async def verify_api_key_header(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    """Dependency to verify API key from header."""
    logger.info(f"[verify_api_key_header] Received X-API-Key header. Key starts with: {x_api_key[:20] if x_api_key else 'NONE'}...")
    user = verify_api_key(db=db, api_key=x_api_key)

    if not user:
        logger.error(f"[verify_api_key_header] API key verification failed. Raising 401 HTTPException")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    logger.info(f"[verify_api_key_header] API key verified successfully for user {user.username}")
    return user


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """
    Create a new conversation.

    Args:
        request: Conversation creation request (optional title)
        user: Authenticated user
        db: Database session

    Returns:
        Created conversation details
    """
    try:
        redis_service = await RedisService.get_instance()
        conversation_service = ConversationService(redis_service)

        conversation = conversation_service.create_conversation(
            user_id=user.id,
            title=request.title,
            db=db,
        )

        logger.info(f"Created conversation {conversation.id} for user {user.id}")

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_active=conversation.is_active,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    active_only: bool = True,
) -> list[ConversationResponse]:
    """
    List conversations for authenticated user.

    Args:
        user: Authenticated user
        db: Database session
        limit: Maximum number of conversations to return
        offset: Pagination offset
        active_only: Only return active conversations

    Returns:
        List of conversation summaries
    """
    try:
        redis_service = await RedisService.get_instance()
        conversation_service = ConversationService(redis_service)

        conversations = conversation_service.list_conversations(
            user_id=user.id,
            db=db,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )

        # Count total messages for each conversation
        message_counts = {}
        for conv in conversations:
            count = conversation_service.get_conversation_message_count(conv.id, db)
            message_counts[conv.id] = count

        return [
            ConversationResponse(
                id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                is_active=conv.is_active,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=message_counts.get(conv.id, 0),
            )
            for conv in conversations
        ]

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
) -> ConversationDetailResponse:
    """
    Get full conversation with all messages.

    Args:
        conversation_id: ID of conversation to retrieve
        user: Authenticated user
        db: Database session

    Returns:
        Full conversation details with messages
    """
    try:
        redis_service = await RedisService.get_instance()
        conversation_service = ConversationService(redis_service)

        conversation = conversation_service.get_conversation(
            conversation_id, user.id, db
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Load all messages
        messages = conversation_service.get_conversation_messages(
            conversation_id, db
        )

        message_responses = [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                model_used=msg.model_used,
                token_count=msg.token_count,
                tool_executions=msg.tool_executions,
                created_at=msg.created_at,
            )
            for msg in messages
        ]

        return ConversationDetailResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_active=conversation.is_active,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_responses,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation",
        )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationCreate,
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """
    Update conversation title.

    Args:
        conversation_id: ID of conversation to update
        request: Update request (title)
        user: Authenticated user
        db: Database session

    Returns:
        Updated conversation details
    """
    try:
        redis_service = await RedisService.get_instance()
        conversation_service = ConversationService(redis_service)

        conversation = conversation_service.update_conversation(
            conversation_id=conversation_id,
            user_id=user.id,
            db=db,
            title=request.title,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        logger.info(f"Updated conversation {conversation_id}")

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_active=conversation.is_active,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation",
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
) -> None:
    """
    Archive (soft delete) a conversation.

    Args:
        conversation_id: ID of conversation to archive
        user: Authenticated user
        db: Database session
    """
    try:
        redis_service = await RedisService.get_instance()
        conversation_service = ConversationService(redis_service)

        conversation = conversation_service.archive_conversation(
            conversation_id=conversation_id,
            user_id=user.id,
            db=db,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        logger.info(f"Archived conversation {conversation_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )


@router.post("/{conversation_id}/clear", response_model=ConversationResponse)
async def clear_conversation(
    conversation_id: str,
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """
    Clear all messages from a conversation (soft reset).

    Args:
        conversation_id: ID of conversation to clear
        user: Authenticated user
        db: Database session

    Returns:
        Cleared conversation details
    """
    try:
        redis_service = await RedisService.get_instance()
        conversation_service = ConversationService(redis_service)

        conversation = conversation_service.clear_conversation(
            conversation_id=conversation_id,
            user_id=user.id,
            db=db,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        logger.info(f"Cleared conversation {conversation_id}")

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_active=conversation.is_active,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear conversation",
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a conversation and all its messages (hard delete).

    Args:
        conversation_id: ID of conversation to delete
        user: Authenticated user
        db: Database session

    Returns:
        None (204 No Content)
    """
    try:
        redis_service = await RedisService.get_instance()
        conversation_service = ConversationService(redis_service)

        # Verify conversation exists and belongs to user
        conversation = conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user.id,
            db=db,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Delete all messages in the conversation
        db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete(synchronize_session=False)

        # Delete the conversation
        db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).delete(synchronize_session=False)

        db.commit()

        # Invalidate Redis cache
        if redis_service:
            cache_key = get_conversation_cache_key(conversation_id)
            try:
                await redis_service.delete(cache_key)
            except Exception as e:
                logger.warning(f"Failed to invalidate cache: {e}")

        logger.info(f"Deleted conversation {conversation_id} for user {user.id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )
