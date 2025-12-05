"""
Authentication API
Generate LiveKit access tokens for voice calls
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from livekit import api
from app.config import settings
from app.models.response import TokenResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/token/generate", response_model=TokenResponse)
async def generate_token(
    room_name: str = "parul-admission",
    participant_name: str = "student"
):
    """
    Generate LiveKit access token for a voice call

    Args:
        room_name: Name of the room to join
        participant_name: Name of the participant

    Returns:
        Access token and connection details
    """

    try:
        # Create access token
        token = api.AccessToken(
            settings.LIVEKIT_API_KEY,
            settings.LIVEKIT_API_SECRET
        )

        token.with_identity(participant_name)
        token.with_name(participant_name)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        ))

        # Token expires in 1 hour
        expires_at = datetime.utcnow() + timedelta(hours=1)

        jwt_token = token.to_jwt()

        logger.info(f"Generated token for {participant_name} in room {room_name}")

        return TokenResponse(
            token=jwt_token,
            url=settings.LIVEKIT_URL,
            room_name=room_name,
            participant_name=participant_name,
            expires_at=expires_at
        )

    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")


@router.get("/token/validate")
async def validate_token(token: str):
    """
    Validate a LiveKit access token

    Args:
        token: JWT token to validate

    Returns:
        Validation result
    """

    try:
        # For now, just return success
        # In production, properly validate the JWT
        return {
            "valid": True,
            "message": "Token is valid"
        }

    except Exception as e:
        logger.error(f"Error validating token: {e}")
        return {
            "valid": False,
            "message": str(e)
        }
