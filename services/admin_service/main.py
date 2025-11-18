"""
Admin Service - FAQ Management
Provides API for creating, updating, and deleting FAQ entries with TTS generation
"""
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.config_loader import config
from shared.models import FAQCreate, FAQUpdate, FAQResponse, FAQDelete, IntentCreate, IntentUpdate, IntentResponse, HealthResponse
from services.admin_service.faq_manager import faq_manager
from services.admin_service.intent_manager import intent_manager
from services.admin_service.tts_generator import tts_generator

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
    Create a new FAQ entry with asynchronous TTS generation

    Args:
        faq: FAQ creation data

    Returns:
        Created FAQ with audio status (audio_status: pending)
        Audio will be generated asynchronously in the background
    """
    import asyncio

    try:
        # Create FAQ with pending audio status
        result = await faq_manager.create_faq(
            question=faq.question,
            answer=faq.answer,
            alternative_questions=faq.alternative_questions or [],
            language=faq.language,
            category=faq.category,
            generate_audio_async=True  # Enable async generation
        )

        # Schedule truly async background task (not blocking the response)
        asyncio.create_task(
            faq_manager.generate_audio_for_faq(
                answer_id=result.answer_id,
                answer_text=faq.answer,
                language=faq.language
            )
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
    Create a new FAQ entry with uploaded audio file or async TTS generation

    Args:
        question: Main question
        answer: Answer text
        alternative_questions: JSON array of alternative questions
        language: Language code
        category: FAQ category
        audio_file: Optional pre-recorded audio file

    Returns:
        Created FAQ with audio status
    """
    import asyncio

    try:
        # Parse alternative questions
        alt_questions = json.loads(alternative_questions) if alternative_questions else []

        # Read audio file if provided
        audio_bytes = None
        if audio_file:
            audio_bytes = await audio_file.read()

        # Create FAQ (synchronous if audio uploaded, async if TTS needed)
        result = await faq_manager.create_faq(
            question=question,
            answer=answer,
            alternative_questions=alt_questions,
            language=language,
            category=category,
            audio_bytes=audio_bytes,
            generate_audio_async=not audio_bytes  # Async only if no audio uploaded
        )

        # If no audio uploaded, schedule truly async background TTS generation
        if not audio_bytes:
            asyncio.create_task(
                faq_manager.generate_audio_for_faq(
                    answer_id=result.answer_id,
                    answer_text=answer,
                    language=language
                )
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

        result = await faq_manager.update_faq(answer_id, update_dict)

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
                result = await faq_manager.create_faq(
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


@app.post("/admin/regenerate_all_audio")
async def regenerate_all_audio():
    """
    Regenerate audio files for all FAQs
    Useful when switching TTS models or fixing missing audio files
    """
    try:
        result = await faq_manager.regenerate_all_audio()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio regeneration failed: {str(e)}")


@app.post("/admin/preview_audio")
async def preview_audio(
    text: str = Form(...),
    language: str = Form(default="auto")
):
    """
    Preview TTS audio without saving to database

    Args:
        text: Text to convert to speech
        language: Language for TTS

    Returns:
        Audio file path for preview
    """
    try:
        import uuid
        import tempfile
        from pathlib import Path

        # Generate temporary audio file
        temp_filename = f"preview_{uuid.uuid4().hex}.wav"
        temp_path = Path(tempfile.gettempdir()) / temp_filename

        # Generate audio using the underlying model directly
        if tts_generator.model is None:
            raise RuntimeError("TTS model not available")

        if hasattr(tts_generator.model, 'generate'):
            import inspect
            if inspect.iscoroutinefunction(tts_generator.model.generate):
                await tts_generator.model.generate(
                    text=text,
                    output_path=str(temp_path),
                    language=language
                )
            else:
                tts_generator.model.generate(
                    text=text,
                    output_path=str(temp_path),
                    language=language
                )
            audio_path = str(temp_path)
        else:
            raise RuntimeError("TTS model does not support audio generation")

        # Return file for streaming
        from fastapi.responses import FileResponse
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"inline; filename=preview.wav",
                "Cache-Control": "no-cache"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio preview failed: {str(e)}")


@app.get("/admin/stats")
async def get_stats():
    """Get admin service statistics"""
    try:
        faqs = faq_manager.list_faqs()
        intents = intent_manager.list_intents()
        return {
            "total_faqs": len(faqs),
            "total_intents": len(intents),
            "categories": list(set(faq.category for faq in faqs)),
            "languages": list(set(faq.language for faq in faqs))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/admin/stats/dashboard")
async def get_dashboard_stats():
    """Get dashboard analytics statistics"""
    try:
        from shared.database import db
        from shared.models import DashboardStats

        # Get query statistics from database
        stats = db.get_query_stats(days=7)

        return DashboardStats(
            today_queries=stats['today_queries'],
            total_queries=stats['total_queries'],
            avg_response_time=stats['avg_response_time'],
            top_faqs=stats['top_faqs'],
            intent_distribution=stats['intent_distribution'],
            daily_trend=stats['daily_trend']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")


@app.get("/admin/query_logs")
async def get_query_logs(
    limit: int = 100,
    offset: int = 0,
    matched_type: Optional[str] = None
):
    """Get query logs with optional filtering and pagination"""
    try:
        from shared.database import db

        logs = db.get_query_logs(limit=limit, offset=offset, matched_type=matched_type)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query logs: {str(e)}")


# ============================================
# Intent Management Endpoints
# ============================================

@app.post("/admin/intent", response_model=IntentResponse)
async def create_intent(intent: IntentCreate):
    """
    Create a new intent entry

    Args:
        intent: Intent creation data

    Returns:
        Created intent
    """
    try:
        result = intent_manager.create_intent(
            intent_name=intent.intent_name,
            description=intent.description,
            trigger_phrases=intent.trigger_phrases,
            action_type=intent.action_type,
            action_config=intent.action_config,
            language=intent.language,
            category=intent.category
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent creation failed: {str(e)}")


@app.get("/admin/intent/{intent_id}", response_model=IntentResponse)
async def get_intent(intent_id: str):
    """Get intent by ID"""
    result = intent_manager.get_intent(intent_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Intent not found: {intent_id}")

    return result


@app.get("/admin/intents", response_model=List[IntentResponse])
async def list_intents():
    """List all intent entries"""
    try:
        return intent_manager.list_intents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list intents: {str(e)}")


@app.put("/admin/intent/{intent_id}", response_model=IntentResponse)
async def update_intent(intent_id: str, updates: IntentUpdate):
    """
    Update intent entry

    Args:
        intent_id: Intent ID
        updates: Fields to update

    Returns:
        Updated intent
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        update_dict = updates.dict(exclude_none=True)

        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")

        result = intent_manager.update_intent(intent_id, update_dict)

        if not result:
            raise HTTPException(status_code=404, detail=f"Intent not found: {intent_id}")

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent update failed: {str(e)}")


@app.delete("/admin/intent/{intent_id}")
async def delete_intent(intent_id: str):
    """
    Delete intent entry

    Args:
        intent_id: Intent ID

    Returns:
        Deletion confirmation
    """
    try:
        success = intent_manager.delete_intent(intent_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Intent not found: {intent_id}")

        return {
            "status": "success",
            "message": f"Intent deleted: {intent_id}",
            "note": "Remember to rebuild search indices in the retrieval service"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent deletion failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    admin_config = config.get_section('admin')
    port = admin_config.get('port', 8003)
    uvicorn.run(app, host="0.0.0.0", port=port)
