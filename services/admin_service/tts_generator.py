"""
TTS Generator for SpeakSense
Text-to-Speech generation with model switching capability
"""
import os
from pathlib import Path
from typing import Optional
import sys
import hashlib
import uuid

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.config_loader import config


class TTSModelFactory:
    """Factory for creating TTS models based on configuration"""

    @staticmethod
    def create_model(model_type: str, **kwargs):
        """Create TTS model based on type"""
        if model_type.lower() == "paddlespeech":
            return PaddleSpeechTTS(**kwargs)
        elif model_type.lower() == "edge-tts":
            return EdgeTTS(**kwargs)
        else:
            # Default to a simple TTS or raise error
            raise ValueError(f"Unsupported TTS model type: {model_type}")


class PaddleSpeechTTS:
    """PaddleSpeech TTS wrapper"""

    def __init__(self, language: str = "auto", speed: float = 1.0, volume: float = 1.0):
        self.language = language
        self.speed = speed
        self.volume = volume
        self.synthesizer = None

    def _load_model(self, lang: str = "zh"):
        """Load PaddleSpeech model"""
        try:
            from paddlespeech.cli.tts.infer import TTSExecutor

            if self.synthesizer is None:
                print(f"Loading PaddleSpeech TTS model for language: {lang}...")
                self.synthesizer = TTSExecutor()
                print("PaddleSpeech TTS model loaded!")
        except ImportError:
            print("Warning: PaddleSpeech not installed. TTS generation will not work.")
            print("Install with: pip install paddlespeech paddlepaddle")
            raise

    def generate(
        self,
        text: str,
        output_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Generate speech from text

        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            language: Language override

        Returns:
            Path to generated audio file
        """
        lang = language or self.language

        # Auto-detect language if needed
        if lang == "auto":
            # Simple detection based on Chinese characters
            import re
            if re.search(r'[\u4e00-\u9fff]', text):
                lang = "zh"
            else:
                lang = "en"

        # Load model for the language
        self._load_model(lang)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            # Generate speech
            self.synthesizer(
                text=text,
                output=output_path,
                am='fastspeech2_csmsc' if lang == 'zh' else 'fastspeech2_ljspeech',
                voc='pwgan_csmsc' if lang == 'zh' else 'pwgan_ljspeech',
                lang=lang,
                sample_rate=24000,
                spk_id=0
            )

            return output_path

        except Exception as e:
            print(f"TTS generation failed: {e}")
            raise


class EdgeTTS:
    """Microsoft Edge TTS wrapper (requires internet)"""

    def __init__(self, language: str = "auto", **kwargs):
        self.language = language

    def generate(
        self,
        text: str,
        output_path: str,
        language: Optional[str] = None
    ) -> str:
        """Generate speech using Edge TTS"""
        try:
            import edge_tts
            import asyncio

            lang = language or self.language

            # Auto-detect language
            if lang == "auto":
                import re
                if re.search(r'[\u4e00-\u9fff]', text):
                    lang = "zh"
                    voice = "zh-CN-XiaoxiaoNeural"
                else:
                    lang = "en"
                    voice = "en-US-AriaNeural"
            elif lang == "zh":
                voice = "zh-CN-XiaoxiaoNeural"
            else:
                voice = "en-US-AriaNeural"

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Generate speech (async)
            async def _generate():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_path)

            asyncio.run(_generate())

            return output_path

        except ImportError:
            print("Warning: edge-tts not installed. Install with: pip install edge-tts")
            raise


class TTSGenerator:
    """Main TTS generator with model switching capability"""

    def __init__(self):
        tts_config = config.get_section('tts')
        admin_config = config.get_section('admin')

        self.model_type = tts_config.get('model_type', 'paddlespeech')
        self.language = tts_config.get('language', 'auto')
        self.speed = tts_config.get('speed', 1.0)
        self.volume = tts_config.get('volume', 1.0)
        self.sample_rate = tts_config.get('sample_rate', 24000)

        self.output_dir = admin_config.get('audio_output_dir', './data/audio_files')
        self.audio_format = admin_config.get('audio_format', 'wav')

        # Ensure output directory exists
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # Initialize TTS model
        try:
            self.model = TTSModelFactory.create_model(
                self.model_type,
                language=self.language,
                speed=self.speed,
                volume=self.volume
            )
        except Exception as e:
            print(f"Warning: Failed to initialize TTS model: {e}")
            self.model = None

    def generate_audio(
        self,
        text: str,
        answer_id: str,
        language: Optional[str] = None
    ) -> str:
        """
        Generate audio file for answer text

        Args:
            text: Answer text to synthesize
            answer_id: Unique answer ID
            language: Language override

        Returns:
            Relative path to generated audio file
        """
        if self.model is None:
            # Create a dummy audio file path if TTS is not available
            print("Warning: TTS model not available, returning placeholder path")
            return f"audio_files/{answer_id}.{self.audio_format}"

        # Generate filename
        filename = f"{answer_id}.{self.audio_format}"
        output_path = os.path.join(self.output_dir, filename)

        # Generate audio
        self.model.generate(
            text=text,
            output_path=output_path,
            language=language
        )

        # Return relative path
        return f"audio_files/{filename}"

    def save_uploaded_audio(
        self,
        audio_bytes: bytes,
        answer_id: str
    ) -> str:
        """
        Save uploaded audio file

        Args:
            audio_bytes: Audio file bytes
            answer_id: Unique answer ID

        Returns:
            Relative path to saved audio file
        """
        # Detect format from bytes (simple check)
        # This is a simple heuristic, can be improved
        if audio_bytes[:4] == b'RIFF':
            ext = 'wav'
        elif audio_bytes[:3] == b'ID3' or audio_bytes[:2] == b'\xff\xfb':
            ext = 'mp3'
        else:
            ext = self.audio_format

        filename = f"{answer_id}.{ext}"
        output_path = os.path.join(self.output_dir, filename)

        # Save file
        with open(output_path, 'wb') as f:
            f.write(audio_bytes)

        return f"audio_files/{filename}"

    def switch_model(self, model_type: str):
        """Switch to a different TTS model"""
        self.model_type = model_type
        self.model = TTSModelFactory.create_model(
            self.model_type,
            language=self.language,
            speed=self.speed,
            volume=self.volume
        )


# Global TTS generator instance
tts_generator = TTSGenerator()
