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
        updated_at: datetime
    ):
        self.answer_id = answer_id
        self.question = question
        self.answer = answer
        self.alternative_questions = alternative_questions
        self.language = language
        self.category = category
        self.audio_path = audio_path
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
