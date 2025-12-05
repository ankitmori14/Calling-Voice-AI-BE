"""
User-related Pydantic models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserContact(BaseModel):
    """User contact information"""
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = None


class UserProfile(BaseModel):
    """User profile information"""
    user_id: str = Field(..., description="Unique user identifier")
    name: Optional[str] = None
    user_type: Optional[str] = Field(None, description="student|parent|guardian")
    language: str = Field(default="english", description="Preferred language")
    contact: UserContact = Field(default_factory=UserContact)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserInterests(BaseModel):
    """User's expressed interests"""
    courses: List[str] = Field(default_factory=list)
    topics_discussed: List[str] = Field(default_factory=list)
    questions_asked: int = 0
    scholarship_percentage: Optional[float] = None
    selected_course: Optional[str] = None


class UserPreferences(BaseModel):
    """User preferences"""
    callback_requested: bool = False
    campus_visit_requested: bool = False
    brochure_requested: bool = False
    preferred_contact_method: Optional[str] = None
    preferred_callback_time: Optional[str] = None
