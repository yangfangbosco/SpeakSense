"""
ASR Service - Automatic Speech Recognition
Provides API for converting audio to text using Whisper
Supports both file upload and WebSocket streaming with VAD
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sys
from pathlib import Path
import numpy as np
import json
import tempfile
import os
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.config_loader import config
from shared.models import ASRResponse, HealthResponse, ErrorResponse
from services.asr_service.asr_model import ASRModel
from services.asr_service.vad_detector import VADDetector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


@app.websocket("/asr/stream")
async def websocket_streaming_asr(websocket: WebSocket):
    """
    WebSocket endpoint for streaming ASR with automatic VAD-based segmentation

    Protocol:
    1. Client connects and sends audio chunks (PCM 16kHz mono, int16)
    2. Server processes with VAD, detects speech segments
    3. When silence detected (speech ends), server transcribes and sends result
    4. Server sends status updates: "speaking", "silence", "transcribing"

    Message format (JSON):
    - From client: {"type": "audio", "data": base64_encoded_audio}
    - From server: {"type": "status", "status": "speaking|silence|transcribing"}
    - From server: {"type": "result", "text": "...", "language": "..."}
    - From server: {"type": "error", "message": "..."}
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    # Default VAD configuration (can be overridden by client)
    vad_config = {
        'threshold': 0.6,
        'min_speech_duration_ms': 400,
        'min_silence_for_sentence_ms': 500,
        'min_silence_for_session_ms': 1500
    }
    vad = None  # Will be initialized after receiving config or with defaults

    try:
        while True:
            # Receive message from client
            message = await websocket.receive_json()

            if message.get("type") == "config":
                # Receive and apply VAD configuration from client
                client_config = message.get("config", {})
                vad_config.update(client_config)
                logger.info(f"Received VAD config: {vad_config}")

                # Initialize VAD with custom config
                vad = VADDetector(
                    sample_rate=16000,
                    threshold=vad_config['threshold'],
                    min_speech_duration_ms=vad_config['min_speech_duration_ms'],
                    min_silence_for_sentence_ms=vad_config['min_silence_for_sentence_ms'],
                    min_silence_for_session_ms=vad_config['min_silence_for_session_ms'],
                    speech_pad_ms=30
                )
                logger.info("VAD detector initialized with custom config")

                # Send acknowledgment
                await websocket.send_json({
                    "type": "config_ack",
                    "config": vad_config
                })

            elif message.get("type") == "audio":
                # Initialize VAD with defaults if not yet initialized
                if vad is None:
                    logger.warning("VAD not initialized, using default config")
                    vad = VADDetector(
                        sample_rate=16000,
                        threshold=vad_config['threshold'],
                        min_speech_duration_ms=vad_config['min_speech_duration_ms'],
                        min_silence_for_sentence_ms=vad_config['min_silence_for_sentence_ms'],
                        min_silence_for_session_ms=vad_config['min_silence_for_session_ms'],
                        speech_pad_ms=30
                    )
                # Decode base64 audio data
                import base64
                audio_data = base64.b64decode(message["data"])

                # Convert bytes to numpy array (assuming int16 PCM)
                audio_chunk = np.frombuffer(audio_data, dtype=np.int16)

                # Process with VAD (now returns 4 values)
                is_speaking, sentence_ended, session_ended, complete_audio = vad.process_chunk(audio_chunk)

                # Send status update
                if is_speaking and not sentence_ended:
                    await websocket.send_json({
                        "type": "status",
                        "status": "speaking"
                    })

                # If sentence or session ended, transcribe it
                if sentence_ended and complete_audio is not None:
                    audio_duration_sec = len(complete_audio) / 16000
                    logger.info(f"Speech segment ended, transcribing {len(complete_audio)} samples ({audio_duration_sec:.2f}s)...")

                    # Send transcribing status
                    await websocket.send_json({
                        "type": "status",
                        "status": "transcribing"
                    })

                    try:
                        # Save to temporary WAV file
                        import wave
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                            temp_path = temp_wav.name

                            # Write WAV file
                            with wave.open(temp_path, 'wb') as wav_file:
                                wav_file.setnchannels(1)  # Mono
                                wav_file.setsampwidth(2)  # 16-bit
                                wav_file.setframerate(16000)  # 16kHz

                                # Convert float32 (-1.0 to 1.0) to int16 (-32768 to 32767)
                                audio_int16 = (complete_audio * 32767).astype(np.int16)
                                wav_file.writeframes(audio_int16.tobytes())

                        # Transcribe
                        result = asr_model.transcribe(
                            audio_path=temp_path,
                            language=None  # Auto-detect
                        )

                        # Clean up temp file
                        os.remove(temp_path)

                        # Only send result if we got actual text (filter out empty/whitespace-only results)
                        transcribed_text = result['text'].strip()
                        if transcribed_text:
                            # Send result with session_ended flag
                            await websocket.send_json({
                                "type": "result",
                                "text": transcribed_text,
                                "language": result.get('language', 'unknown'),
                                "session_ended": session_ended  # Tell client if this is the final result
                            })

                            if session_ended:
                                logger.info(f"Session ended. Final transcription: {transcribed_text}")
                            else:
                                logger.info(f"Sentence transcribed: {transcribed_text}")
                        else:
                            logger.warning(f"Whisper returned empty transcription, skipping result")
                            # Don't send empty results to client

                    except Exception as e:
                        logger.error(f"Transcription error: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Transcription failed: {str(e)}"
                        })

                # If session ended but no audio to transcribe, still notify frontend
                elif session_ended and complete_audio is None:
                    logger.info("Session ended without audio to transcribe, notifying client")
                    await websocket.send_json({
                        "type": "session_end",
                        "message": "Session ended due to prolonged silence"
                    })

            elif message.get("type") == "reset":
                # Reset VAD state
                vad.reset()
                await websocket.send_json({
                    "type": "status",
                    "status": "reset"
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    port = asr_config.get('port', 8001)
    uvicorn.run(app, host="0.0.0.0", port=port)
