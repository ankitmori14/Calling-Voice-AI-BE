"""
Voice Session API
Manage voice conversation sessions
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from app.core.conversation_manager import get_conversation_manager
from app.models.response import VoiceSessionResponse, APIResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/voice", tags=["Voice"])


@router.post("/session/create", response_model=VoiceSessionResponse)
async def create_session(user_id: Optional[str] = None):
    """
    Create a new voice conversation session

    Args:
        user_id: Optional user identifier

    Returns:
        Session details
    """

    try:
        manager = get_conversation_manager()
        session_id = await manager.create_session(user_id)

        logger.info(f"Created voice session: {session_id}")

        return VoiceSessionResponse(
            session_id=session_id,
            status="active",
            room_name="parul-admission",
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get session information

    Args:
        session_id: Session identifier

    Returns:
        Session state and history
    """

    try:
        manager = get_conversation_manager()

        state = await manager.get_session_state(session_id)
        history = await manager.get_conversation_history(session_id)

        if not state:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "state": state,
            "history": history,
            "message_count": len(history)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/message")
async def send_message(session_id: str, message: str):
    """
    Send a message in a voice session (for testing)

    Args:
        session_id: Session identifier
        message: User message

    Returns:
        Assistant's response
    """

    try:
        manager = get_conversation_manager()

        response = await manager.process_message(session_id, message)

        return APIResponse(
            success=True,
            message="Message processed",
            data={
                "response": response,
                "session_id": session_id
            }
        )

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/end")
async def end_session(session_id: str):
    """
    End a voice session

    Args:
        session_id: Session identifier

    Returns:
        Confirmation
    """

    try:
        manager = get_conversation_manager()
        await manager.end_session(session_id)

        return APIResponse(
            success=True,
            message=f"Session {session_id} ended successfully"
        )

    except Exception as e:
        logger.error(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
async def get_history(session_id: str, limit: Optional[int] = None):
    """
    Get conversation history for a session

    Args:
        session_id: Session identifier
        limit: Optional limit on number of messages

    Returns:
        Conversation history
    """

    try:
        manager = get_conversation_manager()
        history = await manager.get_conversation_history(session_id, limit)

        return {
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Import datetime at the top
from datetime import datetime
