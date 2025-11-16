"""
FAQ Manager for SpeakSense Admin Service
Handles CRUD operations for FAQ entries with TTS and vector indexing
"""
from typing import List, Optional, Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import db
from shared.models import FAQCreate, FAQUpdate, FAQResponse, FAQEntry
from services.admin_service.tts_generator import tts_generator


class FAQManager:
    """Manager for FAQ CRUD operations"""

    def __init__(self):
        pass

    def create_faq(
        self,
        question: str,
        answer: str,
        alternative_questions: List[str],
        language: str,
        category: str,
        audio_bytes: Optional[bytes] = None
    ) -> FAQResponse:
        """
        Create a new FAQ entry

        Args:
            question: Main question text
            answer: Answer text
            alternative_questions: List of alternative question phrasings
            language: Language code
            category: FAQ category
            audio_bytes: Optional pre-recorded audio bytes

        Returns:
            FAQResponse with created FAQ information
        """
        # Create FAQ in database first to get answer_id
        faq_entry = db.create_faq(
            question=question,
            answer=answer,
            alternative_questions=alternative_questions,
            language=language,
            category=category,
            audio_path=""  # Temporary, will update after audio generation
        )

        # Generate or save audio
        try:
            if audio_bytes:
                # Save uploaded audio
                audio_path = tts_generator.save_uploaded_audio(
                    audio_bytes=audio_bytes,
                    answer_id=faq_entry.answer_id
                )
            else:
                # Generate audio using TTS
                audio_path = tts_generator.generate_audio(
                    text=answer,
                    answer_id=faq_entry.answer_id,
                    language=language if language != 'auto' else None
                )

            # Update audio path in database
            faq_entry = db.update_faq(
                answer_id=faq_entry.answer_id,
                updates={'audio_path': audio_path}
            )

        except Exception as e:
            print(f"Warning: Audio generation/save failed: {e}")
            # Continue with placeholder audio path
            audio_path = f"audio_files/{faq_entry.answer_id}.wav"
            faq_entry = db.update_faq(
                answer_id=faq_entry.answer_id,
                updates={'audio_path': audio_path}
            )

        # Note: Vector indexing will be done separately via rebuild_indices endpoint
        # This keeps the admin service independent of retrieval service internals

        return self._to_faq_response(faq_entry)

    def get_faq(self, answer_id: str) -> Optional[FAQResponse]:
        """Get FAQ by ID"""
        faq_entry = db.get_faq_by_id(answer_id)

        if faq_entry:
            return self._to_faq_response(faq_entry)
        return None

    def list_faqs(self) -> List[FAQResponse]:
        """List all FAQs"""
        faq_entries = db.get_all_faqs()
        return [self._to_faq_response(entry) for entry in faq_entries]

    def update_faq(
        self,
        answer_id: str,
        updates: Dict
    ) -> Optional[FAQResponse]:
        """
        Update FAQ entry

        Args:
            answer_id: FAQ answer ID
            updates: Dictionary of fields to update

        Returns:
            Updated FAQ response or None if not found
        """
        # If answer text is updated, regenerate audio
        if 'answer' in updates:
            faq_entry = db.get_faq_by_id(answer_id)
            if faq_entry:
                try:
                    audio_path = tts_generator.generate_audio(
                        text=updates['answer'],
                        answer_id=answer_id,
                        language=updates.get('language', faq_entry.language)
                    )
                    updates['audio_path'] = audio_path
                except Exception as e:
                    print(f"Warning: Audio regeneration failed: {e}")

        # Update in database
        faq_entry = db.update_faq(answer_id, updates)

        if faq_entry:
            return self._to_faq_response(faq_entry)
        return None

    def delete_faq(self, answer_id: str) -> bool:
        """
        Delete FAQ entry

        Args:
            answer_id: FAQ answer ID

        Returns:
            True if deleted, False if not found
        """
        # Note: Vector database cleanup should be done via rebuild_indices
        return db.delete_faq(answer_id)

    def _to_faq_response(self, faq_entry: FAQEntry) -> FAQResponse:
        """Convert FAQEntry to FAQResponse"""
        return FAQResponse(
            answer_id=faq_entry.answer_id,
            question=faq_entry.question,
            answer=faq_entry.answer,
            alternative_questions=faq_entry.alternative_questions,
            language=faq_entry.language,
            category=faq_entry.category,
            audio_path=faq_entry.audio_path,
            created_at=faq_entry.created_at,
            updated_at=faq_entry.updated_at
        )


# Global FAQ manager instance
faq_manager = FAQManager()
