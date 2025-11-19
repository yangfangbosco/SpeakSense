"""
TTS Generator for SpeakSense
Text-to-Speech generation with model switching capability
"""
import os
# Set offline mode for transformers/HuggingFace to prevent downloads
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

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
        if model_type.lower() == "edge-tts":
            return EdgeTTS(**kwargs)
        elif model_type.lower() in ["cosyvoice2", "cosyvoice2-0.5b"]:
            return CosyVoice2TTS(**kwargs)
        else:
            raise ValueError(f"Unsupported TTS model type: {model_type}. Only 'edge-tts' and 'cosyvoice2' are supported.")


class EdgeTTS:
    """Microsoft Edge TTS wrapper (requires internet)"""

    def __init__(self, language: str = "auto", **kwargs):
        self.language = language

    async def generate(
        self,
        text: str,
        output_path: str,
        language: Optional[str] = None
    ) -> str:
        """Generate speech using Edge TTS"""
        try:
            import edge_tts

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
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

            return output_path

        except ImportError:
            print("Warning: edge-tts not installed. Install with: pip install edge-tts")
            raise


class CosyVoice2TTS:
    """
    CosyVoice2 TTS wrapper - Multi-lingual zero-shot voice cloning

    CosyVoice2-0.5B is a powerful TTS model that supports:
    - Multi-language synthesis (Chinese, English, etc.)
    - Zero-shot voice cloning with reference audio
    - High quality natural speech
    - Local inference (no internet required)
    """

    def __init__(self, language: str = "auto", **kwargs):
        self.language = language
        self.model = None
        # Path to locally downloaded CosyVoice2 model
        project_root = Path(__file__).parent.parent.parent
        self.model_dir = project_root / "models" / "CosyVoice2-0.5B"
        self.config_path = self.model_dir / "cosyvoice2.yaml"
        # Reference audio for voice cloning
        self.reference_audio_path = self.model_dir / "reference_speaker.wav"

    def _load_model(self):
        """Load CosyVoice2 model from local checkpoint"""
        if self.model is None:
            try:
                # Add CosyVoice to path
                project_root = Path(__file__).parent.parent.parent
                cosyvoice_path = project_root / "third_party" / "CosyVoice"
                sys.path.insert(0, str(cosyvoice_path))
                sys.path.insert(0, str(cosyvoice_path / "third_party" / "Matcha-TTS"))

                print(f"Loading CosyVoice2 model from: {self.model_dir}...")

                # Check if model exists
                if not self.config_path.exists():
                    raise FileNotFoundError(
                        f"CosyVoice2 model not found at {self.model_dir}\n"
                        f"Please download the model using: python download_cosyvoice_model.py"
                    )

                # Import CosyVoice2
                from cosyvoice.cli.cosyvoice import CosyVoice2

                # Load model
                self.model = CosyVoice2(
                    str(self.model_dir),
                    load_jit=False,
                    load_trt=False,
                    fp16=False
                )

                print("✓ CosyVoice2 model loaded successfully!")

            except ImportError as e:
                print(f"Error importing CosyVoice2: {e}")
                print("Make sure CosyVoice is properly installed in third_party/CosyVoice/")
                raise
            except FileNotFoundError as e:
                print(f"Error: {e}")
                raise
            except Exception as e:
                print(f"Error loading CosyVoice2 model: {e}")
                import traceback
                traceback.print_exc()
                raise

    def _ensure_reference_audio(self):
        """Ensure reference audio exists for voice cloning"""
        if not self.reference_audio_path.exists():
            print("Reference audio not found. Generating with edge-tts...")
            try:
                import asyncio
                import edge_tts
                import soundfile as sf
                import librosa

                # Generate reference audio with edge-tts
                # Using short, natural phrase for better voice cloning
                async def generate_reference():
                    tts = edge_tts.Communicate(
                        '你好，欢迎使用语音问答系统。',
                        'zh-CN-XiaoxiaoNeural'
                    )
                    temp_path = str(self.reference_audio_path) + '.temp.mp3'
                    await tts.save(temp_path)

                    # Convert to proper format (22050 Hz, mono, PCM_16)
                    data, sr = sf.read(temp_path)
                    if len(data.shape) > 1:
                        data = data.mean(axis=1)  # Convert to mono
                    if sr != 22050:
                        data = librosa.resample(data, orig_sr=sr, target_sr=22050)
                    sf.write(str(self.reference_audio_path), data, 22050, subtype='PCM_16')

                    # Clean up temp file
                    import os
                    os.remove(temp_path)
                    print(f"✓ Reference audio generated: {self.reference_audio_path}")

                # Run async function
                asyncio.run(generate_reference())

            except Exception as e:
                print(f"Failed to generate reference audio: {e}")
                # Create a silent reference audio as fallback
                import numpy as np
                import scipy.io.wavfile
                silence = np.zeros(int(22050 * 2), dtype=np.float32)  # 2 seconds of silence
                scipy.io.wavfile.write(str(self.reference_audio_path), 22050, silence)
                print("⚠ Created silent reference audio (voice cloning may not work optimally)")

    def generate(
        self,
        text: str,
        output_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Generate speech from text using CosyVoice2

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
            import re
            if re.search(r'[\u4e00-\u9fff]', text):
                lang = "zh"
            else:
                lang = "en"

        # Load model
        self._load_model()

        # Ensure reference audio exists
        self._ensure_reference_audio()

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            # Load reference audio
            from cosyvoice.utils.file_utils import load_wav
            import torchaudio

            prompt_speech_16k = load_wav(str(self.reference_audio_path), 16000)

            # Generate speech using zero-shot inference
            # Reference text (should match the reference audio content exactly)
            # Using the exact text from reference audio generation
            prompt_text = "你好，欢迎使用语音问答系统。"

            print(f"Generating speech for text: {text[:50]}...")

            # Use inference_zero_shot for voice cloning
            for i, output in enumerate(self.model.inference_zero_shot(
                text,
                prompt_text,
                prompt_speech_16k,
                stream=False
            )):
                # Save audio
                torchaudio.save(
                    output_path,
                    output['tts_speech'],
                    self.model.sample_rate
                )
                print(f"✓ Audio saved to: {output_path}")
                break  # Only take the first output

            return output_path

        except Exception as e:
            print(f"CosyVoice2 generation failed: {e}")
            import traceback
            traceback.print_exc()
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

        output_dir = admin_config.get('audio_output_dir', './data/audio_files')
        self.audio_format = admin_config.get('audio_format', 'wav')

        # Convert to absolute path relative to project root
        if not Path(output_dir).is_absolute():
            project_root = Path(__file__).parent.parent.parent
            self.output_dir = str(project_root / output_dir)
        else:
            self.output_dir = output_dir

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

    async def generate_audio(
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
        if hasattr(self.model.generate, '__call__'):
            # Check if it's async
            import inspect
            if inspect.iscoroutinefunction(self.model.generate):
                await self.model.generate(
                    text=text,
                    output_path=output_path,
                    language=language
                )
            else:
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
