"""
Voice Activity Detection using Silero-VAD
Detects speech segments in audio stream for automatic sentence segmentation
"""
import torch
import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class VADDetector:
    """
    Voice Activity Detection detector using Silero-VAD

    Detects when user is speaking and when they stop (silence detection)
    for automatic audio segmentation in streaming scenarios.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 500,
        speech_pad_ms: int = 30
    ):
        """
        Initialize VAD detector

        Args:
            sample_rate: Audio sample rate (must be 8000 or 16000)
            threshold: Speech probability threshold (0.0-1.0)
            min_speech_duration_ms: Minimum speech duration to consider as speech
            min_silence_duration_ms: Minimum silence duration to trigger speech end
            speech_pad_ms: Padding to add before/after speech segments
        """
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.speech_pad_ms = speech_pad_ms

        # Load Silero-VAD model
        self._load_model()

        # State tracking
        self.reset()

    def _load_model(self):
        """Load Silero-VAD model"""
        try:
            # Load pretrained Silero-VAD model
            logger.info("Loading Silero-VAD model...")
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False  # Use PyTorch version
            )

            # Extract utilities
            (self.get_speech_timestamps,
             self.save_audio,
             self.read_audio,
             self.VADIterator,
             self.collect_chunks) = utils

            logger.info("✓ Silero-VAD model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Silero-VAD model: {e}")
            raise

    def reset(self):
        """Reset detector state"""
        self.audio_buffer = []
        self.is_speaking = False
        self.speech_start_sample = None
        self.silence_start_sample = None
        self.total_samples = 0

    def process_chunk(
        self,
        audio_chunk: np.ndarray
    ) -> Tuple[bool, bool, np.ndarray]:
        """
        Process audio chunk and detect speech/silence

        Args:
            audio_chunk: Audio chunk as numpy array (int16 or float32)

        Returns:
            Tuple of (is_speech_active, speech_ended, complete_audio)
            - is_speech_active: Whether speech is currently detected
            - speech_ended: Whether a complete speech segment ended
            - complete_audio: Complete audio segment if speech_ended, else None
        """
        # Convert to float32 if needed
        if audio_chunk.dtype == np.int16:
            audio_chunk = audio_chunk.astype(np.float32) / 32768.0

        # Silero-VAD requires chunks of exactly 512 samples for 16kHz
        # If we receive larger chunks, split them and average the probabilities
        chunk_size = 512 if self.sample_rate == 16000 else 256
        speech_probs = []

        for i in range(0, len(audio_chunk), chunk_size):
            chunk = audio_chunk[i:i + chunk_size]

            # Pad the last chunk if needed
            if len(chunk) < chunk_size:
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)), mode='constant')

            # Convert to torch tensor
            audio_tensor = torch.from_numpy(chunk)

            # Get speech probability from VAD
            prob = self.model(audio_tensor, self.sample_rate).item()
            speech_probs.append(prob)

        # Use the maximum probability (most conservative approach)
        speech_prob = max(speech_probs) if speech_probs else 0.0

        # Update buffer
        self.audio_buffer.append(audio_chunk)
        chunk_samples = len(audio_chunk)
        self.total_samples += chunk_samples

        # Detect speech start
        if not self.is_speaking and speech_prob >= self.threshold:
            self.is_speaking = True
            self.speech_start_sample = self.total_samples - chunk_samples
            self.silence_start_sample = None
            logger.debug(f"Speech started at sample {self.speech_start_sample}")

        # Detect silence start (potential speech end)
        elif self.is_speaking and speech_prob < self.threshold:
            if self.silence_start_sample is None:
                self.silence_start_sample = self.total_samples - chunk_samples
                logger.debug(f"Silence started at sample {self.silence_start_sample}")

        # Speech continues (reset silence counter)
        elif self.is_speaking and speech_prob >= self.threshold:
            self.silence_start_sample = None

        # Check if speech segment ended
        speech_ended = False
        complete_audio = None

        if self.is_speaking and self.silence_start_sample is not None:
            # Calculate silence duration
            silence_duration_samples = self.total_samples - self.silence_start_sample
            silence_duration_ms = (silence_duration_samples / self.sample_rate) * 1000

            # Check if silence duration exceeds threshold
            if silence_duration_ms >= self.min_silence_duration_ms:
                # Speech segment ended
                logger.debug(f"Speech ended after {silence_duration_ms:.0f}ms of silence")

                # Collect complete audio segment
                complete_audio = np.concatenate(self.audio_buffer)
                speech_ended = True

                # Reset state
                self.reset()

        return self.is_speaking, speech_ended, complete_audio

    def get_speech_timestamps_from_audio(
        self,
        audio: np.ndarray
    ) -> List[dict]:
        """
        Get speech timestamps from complete audio

        Args:
            audio: Complete audio as numpy array

        Returns:
            List of speech segments with 'start' and 'end' timestamps (in seconds)
        """
        # Convert to torch tensor
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0

        audio_tensor = torch.from_numpy(audio)

        # Get speech timestamps
        speech_timestamps = self.get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=self.sample_rate,
            threshold=self.threshold,
            min_speech_duration_ms=self.min_speech_duration_ms,
            min_silence_duration_ms=self.min_silence_duration_ms,
            speech_pad_ms=self.speech_pad_ms
        )

        # Convert to seconds
        for timestamp in speech_timestamps:
            timestamp['start'] = timestamp['start'] / self.sample_rate
            timestamp['end'] = timestamp['end'] / self.sample_rate

        return speech_timestamps
