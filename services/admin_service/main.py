"""
Admin Service - FAQ Management
Provides API for creating, updating, and deleting FAQ entries with TTS generation
"""
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.config_loader import config
from shared.models import FAQCreate, FAQUpdate, FAQResponse, FAQDelete, HealthResponse
from services.admin_service.faq_manager import faq_manager

# Initialize FastAPI app
app = FastAPI(
    title="SpeakSense Admin Service",
    description="FAQ management service with TTS generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        service="Admin Service",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="Admin Service",
        version="1.0.0"
    )


@app.post("/admin/faq", response_model=FAQResponse)
async def create_faq(faq: FAQCreate):
    """
    Create a new FAQ entry with TTS generation

    Args:
        faq: FAQ creation data

    Returns:
        Created FAQ with audio path
    """
    try:
        result = faq_manager.create_faq(
            question=faq.question,
            answer=faq.answer,
            alternative_questions=faq.alternative_questions or [],
            language=faq.language,
            category=faq.category
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ creation failed: {str(e)}")


@app.post("/admin/faq_with_audio", response_model=FAQResponse)
async def create_faq_with_audio(
    question: str = Form(...),
    answer: str = Form(...),
    alternative_questions: Optional[str] = Form(default="[]"),
    language: str = Form(default="auto"),
    category: str = Form(default="general"),
    audio_file: Optional[UploadFile] = File(default=None)
):
    """
    Create a new FAQ entry with uploaded audio file

    Args:
        question: Main question
        answer: Answer text
        alternative_questions: JSON array of alternative questions
        language: Language code
        category: FAQ category
        audio_file: Optional pre-recorded audio file

    Returns:
        Created FAQ with audio path
    """
    try:
        # Parse alternative questions
        alt_questions = json.loads(alternative_questions) if alternative_questions else []

        # Read audio file if provided
        audio_bytes = None
        if audio_file:
            audio_bytes = await audio_file.read()

        result = faq_manager.create_faq(
            question=question,
            answer=answer,
            alternative_questions=alt_questions,
            language=language,
            category=category,
            audio_bytes=audio_bytes
        )

        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid alternative_questions JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ creation failed: {str(e)}")


@app.get("/admin/faq/{answer_id}", response_model=FAQResponse)
async def get_faq(answer_id: str):
    """Get FAQ by ID"""
    result = faq_manager.get_faq(answer_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"FAQ not found: {answer_id}")

    return result


@app.get("/admin/faqs", response_model=List[FAQResponse])
async def list_faqs():
    """List all FAQ entries"""
    try:
        return faq_manager.list_faqs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list FAQs: {str(e)}")


@app.put("/admin/faq/{answer_id}", response_model=FAQResponse)
async def update_faq(answer_id: str, updates: FAQUpdate):
    """
    Update FAQ entry

    Args:
        answer_id: FAQ answer ID
        updates: Fields to update

    Returns:
        Updated FAQ
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        update_dict = updates.dict(exclude_none=True)

        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")

        result = faq_manager.update_faq(answer_id, update_dict)

        if not result:
            raise HTTPException(status_code=404, detail=f"FAQ not found: {answer_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ update failed: {str(e)}")


@app.delete("/admin/faq/{answer_id}")
async def delete_faq(answer_id: str):
    """
    Delete FAQ entry

    Args:
        answer_id: FAQ answer ID

    Returns:
        Deletion confirmation
    """
    try:
        success = faq_manager.delete_faq(answer_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"FAQ not found: {answer_id}")

        return {
            "status": "success",
            "message": f"FAQ deleted: {answer_id}",
            "note": "Remember to rebuild search indices in the retrieval service"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ deletion failed: {str(e)}")


@app.post("/admin/batch_upload")
async def batch_upload_faqs(faqs: List[FAQCreate]):
    """
    Batch upload multiple FAQ entries

    Args:
        faqs: List of FAQ creation data

    Returns:
        Summary of created FAQs
    """
    try:
        created_faqs = []
        errors = []

        for idx, faq in enumerate(faqs):
            try:
                result = faq_manager.create_faq(
                    question=faq.question,
                    answer=faq.answer,
                    alternative_questions=faq.alternative_questions or [],
                    language=faq.language,
                    category=faq.category
                )
                created_faqs.append(result)
            except Exception as e:
                errors.append({
                    "index": idx,
                    "question": faq.question,
                    "error": str(e)
                })

        return {
            "status": "completed",
            "created_count": len(created_faqs),
            "error_count": len(errors),
            "created_faqs": created_faqs,
            "errors": errors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@app.get("/admin/stats")
async def get_stats():
    """Get admin service statistics"""
    try:
        faqs = faq_manager.list_faqs()
        return {
            "total_faqs": len(faqs),
            "categories": list(set(faq.category for faq in faqs)),
            "languages": list(set(faq.language for faq in faqs))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    admin_config = config.get_section('admin')
    port = admin_config.get('port', 8003)
    uvicorn.run(app, host="0.0.0.0", port=port)
