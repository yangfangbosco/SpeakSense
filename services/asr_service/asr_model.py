"""
ASR Model Wrapper for SpeakSense
Supports Whisper and other ASR models with easy switching
"""
import torch
from pathlib import Path
from typing import Dict, Optional
import tempfile
import os

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("Warning: faster-whisper not available, falling back to openai-whisper")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: openai-whisper not available")


class ASRModelFactory:
    """Factory for creating ASR models based on configuration"""

    @staticmethod
    def create_model(model_type: str, model_name: str, device: str = "cpu"):
        """Create ASR model based on type"""
        if model_type.lower() == "faster-whisper":
            if not FASTER_WHISPER_AVAILABLE:
                raise ImportError("faster-whisper is not installed. Run: pip install faster-whisper")
            return FasterWhisperASR(model_name, device)
        elif model_type.lower() == "whisper":
            if not WHISPER_AVAILABLE:
                raise ImportError("openai-whisper is not installed. Run: pip install openai-whisper")
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
        """Load Whisper model from local directory or download"""
        # Check for local model first
        project_root = Path(__file__).parent.parent.parent
        local_model_dir = project_root / "models" / "whisper"
        local_model_path = local_model_dir / f"{self.model_name}.pt"

        if local_model_path.exists():
            print(f"Loading Whisper model from local path: {local_model_path}")
            self.model = whisper.load_model(self.model_name, device=self.device, download_root=str(local_model_dir))
        else:
            print(f"Loading Whisper model: {self.model_name} on {self.device}...")
            print(f"(To use local model, place {self.model_name}.pt in: {local_model_dir})")
            self.model = whisper.load_model(self.model_name, device=self.device, download_root=str(local_model_dir))

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


class FasterWhisperASR:
    """Faster-whisper ASR model wrapper - 4-5x faster than openai-whisper"""

    def __init__(self, model_name: str = "base", device: str = "cpu"):
        """
        Initialize Faster-whisper model

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to run on (cpu, cuda, auto)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Faster-whisper model from project directory"""
        # Map device
        if self.device == "cuda" and not torch.cuda.is_available():
            print("CUDA not available, falling back to CPU")
            device = "cpu"
        else:
            device = self.device

        # Determine compute type based on device
        if device == "cuda":
            compute_type = "float16"  # Use FP16 on GPU for speed
        else:
            compute_type = "int8"  # Use INT8 on CPU for speed

        print(f"Loading Faster-whisper model: {self.model_name} on {device} with {compute_type}...")

        # Get project root directory
        project_root = Path(__file__).parent.parent.parent
        model_cache_dir = project_root / "models" / f"faster-whisper-{self.model_name}"

        # Check if model exists in project directory
        if model_cache_dir.exists():
            # Find the actual model path in snapshots
            snapshots_dir = model_cache_dir / "snapshots"
            if snapshots_dir.exists():
                # Get the first (and usually only) snapshot
                snapshot_dirs = list(snapshots_dir.iterdir())
                if snapshot_dirs:
                    model_path = snapshot_dirs[0]
                    print(f"Loading from local path: {model_path}")
                    # Load from project directory
                    self.model = WhisperModel(
                        str(model_path),
                        device=device,
                        compute_type=compute_type,
                        local_files_only=True
                    )
                    return

            print(f"Warning: Model cache found but no snapshot directory, trying direct load...")
        else:
            # Fallback: download to project directory
            print(f"Model not found locally, downloading to project directory...")
            download_root = project_root / "models"
            download_root.mkdir(parents=True, exist_ok=True)
            self.model = WhisperModel(
                self.model_name,
                device=device,
                compute_type=compute_type,
                download_root=str(download_root)
            )

        print(f"Faster-whisper model loaded successfully!")

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
        options = {}
        if language and language != "auto":
            options["language"] = language

        # Transcribe with faster-whisper
        # Returns: (segments, info)
        segments, info = self.model.transcribe(
            audio_path,
            task=task,
            **options
        )

        # Collect all segments
        text_parts = []
        segments_list = []

        for segment in segments:
            text_parts.append(segment.text)
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })

        full_text = " ".join(text_parts).strip()

        return {
            "text": full_text,
            "language": info.language if hasattr(info, 'language') else language,
            "segments": segments_list
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
        Switch to a different Faster-whisper model

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
