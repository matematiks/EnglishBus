"""
Pydantic models for API request/response validation
Based on API_CONTRACT.md v1.0.0
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ============================================
# REQUEST MODELS
# ============================================

class LoginRequest(BaseModel):
    """Simple login with username"""
    username: str = Field(..., min_length=1, max_length=50)


class SessionStartRequest(BaseModel):
    """Request to start a new learning session"""
    user_id: int = Field(..., gt=0, description="User ID")
    course_id: int = Field(..., gt=0, description="Course ID")
    unit_id: Optional[int] = Field(None, description="Optional: Limit session to specific unit")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "course_id": 1,
                "unit_id": 2
            }
        }



from typing import List, Optional, Union

class SessionCompleteRequest(BaseModel):
    """Request to complete a session and update progress"""
    user_id: int = Field(..., gt=0)
    course_id: int = Field(..., gt=0)
    # Allow strings for 'sent_X' logic in Practice Mode
    completed_word_ids: List[Union[int, str]] = Field(..., min_length=1, description="IDs of completed words")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "course_id": 1,
                "completed_word_ids": [1, 2, 3, 4, 5]
            }
        }


# ============================================
# ADMIN MODELS
# ============================================

class UnitCreateRequest(BaseModel):
    course_id: int
    name: str = Field(..., min_length=1)
    order_number: int

class WordCreateRequest(BaseModel):
    course_id: int
    unit_id: int
    english: str
    turkish: str
    image_url: Optional[str] = None
    audio_en_url: Optional[str] = None
    audio_tr_url: Optional[str] = None
    order_number: int


# --- AUTH MODELS ---
class UserRegisterRequest(BaseModel):
    username: str
    password: str

class UserLoginRequest(BaseModel):
    username: str
    password: str
class ResetRequest(BaseModel):
    course_id: int = Field(..., gt=0)
    password: str = Field(..., min_length=1)



# ============================================
# RESPONSE MODELS
# ============================================

class WordItem(BaseModel):
    """A word item in a learning session"""
    word_id: int
    english: str
    turkish: str
    type: str = Field(..., pattern="^(NEW|REVIEW)$", description="NEW or REVIEW")
    image_url: str
    audio_en_url: str
    audio_tr_url: str
    order_number: int
    repetition_count: Optional[int] = Field(None, description="Only for REVIEW words")
    unit_id: Optional[int] = None
    logical_address: str = Field(..., description="Format: UserID.CourseID.UnitID.OrderNumber (e.g., '36.1.2.17')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "word_id": 45,
                "english": "house",
                "turkish": "ev",
                "type": "NEW",
                "image_url": "kurslar/A1_English/images/045.jpg",
                "audio_en_url": "kurslar/A1_English/ing_audio/ing_045.mp3",
                "audio_tr_url": "kurslar/A1_English/tr_audio/tr_045.mp3",
                "order_number": 45
            }
        }


class SessionStartResponse(BaseModel):
    """Response for session start"""
    session_id: str
    current_step: int
    items: List[dict]
    active_unit_id: Optional[int] = None
    total_count: int = Field(..., description="Total number of items in this session")
    has_more: bool = Field(False, description="True if avalanche guard triggered")
    unit_progress: Optional[dict] = Field(None, description="Progress info for current unit")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_step": 12,
                "items": [],
                "total_count": 15,
                "has_more": False,
                "unit_progress": {"total": 50, "new_words": 15, "seen": 15}
            }
        }


class SessionCompleteResponse(BaseModel):
    """Response for session completion"""
    status: str = "success"
    new_step: int
    words_updated: int
    daily_new_count: int = 0
    unit_completed: bool = False  # True when unit is fully completed
    course_completed: bool = False  # True when entire course is done


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str
    details: Optional[str] = None


# ============================================
# UNIT STATUS MODELS (Progressive Lock)
# ============================================

class UnitProgressModel(BaseModel):
    """Unit progress with two-tier metrics (hybrid approach)"""
    total: int = Field(..., description="Total words in unit")
    seen: int = Field(..., description="Words with rep_count >= 1 (introduced)")
    mastered: int = Field(..., description="Words with rep_count >= 3 (reinforced)")
    seen_percentage: float = Field(..., description="Percentage seen (0-100)")
    mastered_percentage: float = Field(..., description="Percentage mastered (0-100)")


class UnitStatusModel(BaseModel):
    """Unit status and progress"""
    unit_id: int
    name: str
    order: int
    status: str = Field(..., description="OPEN or LOCKED")
    progress: UnitProgressModel


# ============================================
# UNIT GATING MODELS (Optional endpoint)
# ============================================

class UnitProgress(BaseModel):
    """Progress for a single unit"""
    seen_count: int
    mastered_count: int


class UnitsStatusResponse(BaseModel):
    """Response for GET /courses/{id}/units/status"""
    units: List[UnitStatusModel]
    
    class Config:
        json_schema_extra = {
            "example": {
                "units": [
                    {
                        "unit_id": 1,
                        "name": "A1.1",
                        "order": 1,
                        "status": "OPEN",
                        "progress": {"total": 50, "seen": 30, "percentage": 60.0}
                    }
                ]
            }
        }
