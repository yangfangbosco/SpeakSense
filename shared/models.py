"""
Pydantic Models for SpeakSense
Data validation and serialization models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# ============ ASR Service Models ============

class ASRRequest(BaseModel):
    """Request model for ASR transcription"""
    audio_base64: Optional[str] = None
    language: Optional[str] = "auto"  # auto, zh, en


class ASRResponse(BaseModel):
    """Response model for ASR transcription"""
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None


# ============ Retrieval Service Models ============

class RetrievalRequest(BaseModel):
    """Request model for FAQ retrieval"""
    query: str
    top_k: Optional[int] = 1
    language: Optional[str] = "auto"


class RetrievalResponse(BaseModel):
    """Response model for FAQ retrieval"""
    answer_id: str
    question: str
    answer: str
    audio_path: str
    confidence: float
    matched_by: str  # "bm25", "vector", "hybrid"


# ============ Admin Service Models ============

class FAQCreate(BaseModel):
    """Model for creating a new FAQ entry"""
    question: str = Field(..., description="Standard question text")
    answer: str = Field(..., description="Standard answer text")
    alternative_questions: Optional[List[str]] = Field(default=[], description="Alternative phrasings")
    language: str = Field(default="auto", description="Language: zh, en, or auto")
    category: Optional[str] = Field(default="general", description="FAQ category")
    audio_file: Optional[str] = None  # Optional: upload pre-recorded audio instead of TTS


class FAQResponse(BaseModel):
    """Response model for FAQ operations"""
    answer_id: str
    question: str
    answer: str
    alternative_questions: List[str]
    language: str
    category: str
    audio_path: str
    audio_status: str  # pending, generating, completed, failed
    created_at: datetime
    updated_at: datetime


class FAQUpdate(BaseModel):
    """Model for updating an FAQ entry"""
    question: Optional[str] = None
    answer: Optional[str] = None
    alternative_questions: Optional[List[str]] = None
    language: Optional[str] = None
    category: Optional[str] = None


class FAQDelete(BaseModel):
    """Model for deleting an FAQ entry"""
    answer_id: str


# ============ Database Models ============

class FAQEntry:
    """Database model for FAQ entry"""
    def __init__(
        self,
        answer_id: str,
        question: str,
        answer: str,
        alternative_questions: List[str],
        language: str,
        category: str,
        audio_path: str,
        created_at: datetime,
        updated_at: datetime,
        audio_status: str = "pending"
    ):
        self.answer_id = answer_id
        self.question = question
        self.answer = answer
        self.alternative_questions = alternative_questions
        self.language = language
        self.category = category
        self.audio_path = audio_path
        self.audio_status = audio_status  # pending, generating, completed, failed
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict:
        return {
            "answer_id": self.answer_id,
            "question": self.question,
            "answer": self.answer,
            "alternative_questions": self.alternative_questions,
            "language": self.language,
            "category": self.category,
            "audio_path": self.audio_path,
            "audio_status": self.audio_status,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }


# ============ Intent Service Models ============

class IntentCreate(BaseModel):
    """Model for creating a new intent entry"""
    intent_name: str = Field(..., description="Unique intent name (e.g., borrow_book)")
    description: str = Field(..., description="Description of what this intent does")
    trigger_phrases: List[str] = Field(..., description="Phrases that trigger this intent")
    action_type: str = Field(..., description="Type of action: open_app, api_call, navigate, etc.")
    action_config: Dict = Field(default={}, description="Action configuration (app_id, url, params, etc.)")
    language: str = Field(default="auto", description="Language: zh, en, or auto")
    category: Optional[str] = Field(default="general", description="Intent category")


class IntentResponse(BaseModel):
    """Response model for intent operations"""
    intent_id: str
    intent_name: str
    description: str
    trigger_phrases: List[str]
    action_type: str
    action_config: Dict
    language: str
    category: str
    created_at: datetime
    updated_at: datetime


class IntentUpdate(BaseModel):
    """Model for updating an intent entry"""
    intent_name: Optional[str] = None
    description: Optional[str] = None
    trigger_phrases: Optional[List[str]] = None
    action_type: Optional[str] = None
    action_config: Optional[Dict] = None
    language: Optional[str] = None
    category: Optional[str] = None


class IntentEntry:
    """Database model for intent entry"""
    def __init__(
        self,
        intent_id: str,
        intent_name: str,
        description: str,
        trigger_phrases: List[str],
        action_type: str,
        action_config: Dict,
        language: str,
        category: str,
        created_at: datetime,
        updated_at: datetime
    ):
        self.intent_id = intent_id
        self.intent_name = intent_name
        self.description = description
        self.trigger_phrases = trigger_phrases
        self.action_type = action_type
        self.action_config = action_config
        self.language = language
        self.category = category
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict:
        return {
            "intent_id": self.intent_id,
            "intent_name": self.intent_name,
            "description": self.description,
            "trigger_phrases": self.trigger_phrases,
            "action_type": self.action_type,
            "action_config": self.action_config,
            "language": self.language,
            "category": self.category,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }


# ============ Common Response Models ============

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


# ============ Query Logs Models ============

class QueryLog:
    """Query log entry for analytics"""
    def __init__(
        self,
        log_id: str,
        query_text: str,
        matched_type: Optional[str],  # 'faq', 'intent', 'none'
        matched_id: Optional[str],
        matched_question: Optional[str],
        confidence: Optional[float],
        response_time: Optional[float],
        created_at: datetime
    ):
        self.log_id = log_id
        self.query_text = query_text
        self.matched_type = matched_type
        self.matched_id = matched_id
        self.matched_question = matched_question
        self.confidence = confidence
        self.response_time = response_time
        self.created_at = created_at


class QueryLogResponse(BaseModel):
    """Response model for query log"""
    log_id: str
    query_text: str
    matched_type: Optional[str]
    matched_id: Optional[str]
    matched_question: Optional[str]
    confidence: Optional[float]
    response_time: Optional[float]
    created_at: datetime


class DashboardStats(BaseModel):
    """Dashboard statistics response"""
    today_queries: int
    total_queries: int
    avg_response_time: float
    top_faqs: List[Dict]  # [{question, count}, ...]
    intent_distribution: List[Dict]  # [{intent_name, count}, ...]
    daily_trend: List[Dict]  # [{date, count}, ...]
