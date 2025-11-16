"""
ASR Service - Automatic Speech Recognition
Provides API for converting audio to text using Whisper
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.config_loader import config
from shared.models import ASRResponse, HealthResponse, ErrorResponse
from services.asr_service.asr_model import ASRModel

# Initialize FastAPI app
app = FastAPI(
    title="SpeakSense ASR Service",
    description="Automatic Speech Recognition service for SpeakSense",
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

# Initialize ASR model
asr_config = config.get_section('asr')
asr_model = ASRModel(
    model_type=asr_config.get('model_type', 'whisper'),
    model_name=asr_config.get('model_name', 'medium'),
    device=asr_config.get('device', 'cpu')
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        service="ASR Service",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="ASR Service",
        version="1.0.0"
    )


@app.post("/asr/transcribe", response_model=ASRResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default="auto")
):
    """
    Transcribe audio file to text

    Args:
        file: Audio file (MP3, WAV, etc.)
        language: Language code (zh, en, auto)

    Returns:
        Transcription result with text and detected language
    """
    try:
        # Read audio file
        audio_bytes = await file.read()

        # Get file extension
        file_ext = Path(file.filename).suffix.lstrip('.') if file.filename else 'mp3'

        # Transcribe
        result = asr_model.transcribe_from_bytes(
            audio_bytes=audio_bytes,
            language=language if language != "auto" else None,
            audio_format=file_ext
        )

        return ASRResponse(
            text=result['text'],
            language=result.get('language'),
            confidence=None  # Whisper doesn't provide confidence score directly
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/asr/switch_model")
async def switch_model(
    model_name: str,
    device: Optional[str] = None
):
    """
    Switch to a different ASR model

    Args:
        model_name: Model name (tiny, base, small, medium, large)
        device: Device to use (cpu, cuda) - optional

    Returns:
        Success message
    """
    try:
        asr_model.switch_model(model_name=model_name, device=device)
        return {
            "status": "success",
            "message": f"Switched to model: {model_name}",
            "device": device or asr_model.device
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model switch failed: {str(e)}")


@app.get("/asr/info")
async def get_model_info():
    """Get current ASR model information"""
    return {
        "model_type": asr_model.model_type,
        "model_name": asr_model.model_name,
        "device": asr_model.device
    }


if __name__ == "__main__":
    import uvicorn

    port = asr_config.get('port', 8001)
    uvicorn.run(app, host="0.0.0.0", port=port)
