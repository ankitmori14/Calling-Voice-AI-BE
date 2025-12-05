"""
API Response models
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class TokenResponse(BaseModel):
    """LiveKit token response"""
    token: str
    url: str
    room_name: str
    participant_name: str
    expires_at: datetime


class VoiceSessionResponse(BaseModel):
    """Voice session response"""
    session_id: str
    status: str
    room_name: str
    created_at: datetime


class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int = 500
