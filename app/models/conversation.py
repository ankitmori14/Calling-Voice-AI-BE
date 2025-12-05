"""
Conversation state Pydantic models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role types"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentType(str, Enum):
    """Agent types in the workflow"""
    GREETING = "greeting"
    ROUTER = "router"
    COURSE = "course"
    FEES = "fees"
    ADMISSION = "admission"
    FOLLOWUP = "followup"


class ConversationState(BaseModel):
    """LangGraph conversation state"""
    session_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    current_agent: Optional[AgentType] = None
    visited_agents: List[str] = Field(default_factory=list)
    topics_discussed: List[str] = Field(default_factory=list)
    user_info: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    conversation_count: int = 0
    escalation_needed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationSummary(BaseModel):
    """Summary of a conversation session"""
    session_id: str
    user_name: Optional[str] = None
    user_type: Optional[str] = None
    topics_discussed: List[str]
    courses_inquired: List[str]
    total_messages: int
    duration_minutes: Optional[float] = None
    status: str = Field(default="active")  # active|completed|escalated
    created_at: datetime
    ended_at: Optional[datetime] = None
