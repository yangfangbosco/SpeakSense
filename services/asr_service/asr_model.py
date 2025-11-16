"""
ASR Model Wrapper for SpeakSense
Supports Whisper and other ASR models with easy switching
"""
import whisper
import torch
from pathlib import Path
from typing import Dict, Optional
import tempfile
import os


class ASRModelFactory:
    """Factory for creating ASR models based on configuration"""

    @staticmethod
    def create_model(model_type: str, model_name: str, device: str = "cpu"):
        """Create ASR model based on type"""
        if model_type.lower() == "whisper":
            return WhisperASR(model_name, device)
        else:
            raise ValueError(f"Unsupported ASR model type: {model_type}")


class WhisperASR:
    """Whisper ASR model wrapper"""

    def __init__(self, model_name: str = "medium", device: str = "cpu"):
        """
        Initialize Whisper model

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Whisper model"""
        print(f"Loading Whisper model: {self.model_name} on {self.device}...")
        self.model = whisper.load_model(self.model_name, device=self.device)
        print(f"Whisper model loaded successfully!")

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict:
        """
        Transcribe audio file

        Args:
            audio_path: Path to audio file
            language: Language code (zh, en, etc.) or None for auto-detection
            task: "transcribe" or "translate"

        Returns:
            Dictionary with transcription results
        """
        if self.model is None:
            self._load_model()

        # Prepare options
        options = {"task": task}
        if language and language != "auto":
            options["language"] = language

        # Transcribe
        result = self.model.transcribe(audio_path, **options)

        return {
            "text": result["text"].strip(),
            "language": result.get("language", language),
            "segments": result.get("segments", [])
        }

    def transcribe_from_bytes(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        task: str = "transcribe",
        audio_format: str = "mp3"
    ) -> Dict:
        """
        Transcribe audio from bytes

        Args:
            audio_bytes: Audio file bytes
            language: Language code or None for auto-detection
            task: "transcribe" or "translate"
            audio_format: Audio format (mp3, wav, etc.)

        Returns:
            Dictionary with transcription results
        """
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            # Transcribe
            result = self.transcribe(temp_path, language, task)
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def switch_model(self, model_name: str, device: str = None):
        """
        Switch to a different Whisper model

        Args:
            model_name: New model name
            device: Device to use (optional, defaults to current device)
        """
        self.model_name = model_name
        if device:
            self.device = device

        # Unload current model
        if self.model is not None:
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        # Load new model
        self._load_model()


class ASRModel:
    """Main ASR model class with model switching capability"""

    def __init__(self, model_type: str = "whisper", model_name: str = "medium", device: str = "cpu"):
        self.model_type = model_type
        self.model_name = model_name
        self.device = device
        self.model = ASRModelFactory.create_model(model_type, model_name, device)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict:
        """Transcribe audio file"""
        return self.model.transcribe(audio_path, language)

    def transcribe_from_bytes(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        audio_format: str = "mp3"
    ) -> Dict:
        """Transcribe audio from bytes"""
        return self.model.transcribe_from_bytes(audio_bytes, language, audio_format=audio_format)

    def switch_model(self, model_type: str = None, model_name: str = None, device: str = None):
        """Switch to a different ASR model"""
        if model_type and model_type != self.model_type:
            # Switch model type
            self.model_type = model_type
            self.model_name = model_name or "medium"
            self.device = device or self.device
            self.model = ASRModelFactory.create_model(self.model_type, self.model_name, self.device)
        elif model_name and hasattr(self.model, 'switch_model'):
            # Switch model within same type
            self.model.switch_model(model_name, device)
        else:
            raise ValueError("Must provide either model_type or model_name to switch")
