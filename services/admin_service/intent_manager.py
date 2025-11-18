"""
Intent Manager for SpeakSense Admin Service
Handles CRUD operations for intent entries
"""
from typing import List, Optional, Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import db
from shared.models import IntentCreate, IntentUpdate, IntentResponse, IntentEntry


class IntentManager:
    """Manager for Intent CRUD operations"""

    def __init__(self):
        pass

    def create_intent(
        self,
        intent_name: str,
        description: str,
        trigger_phrases: List[str],
        action_type: str,
        action_config: Dict,
        language: str,
        category: str
    ) -> IntentResponse:
        """
        Create a new intent entry

        Args:
            intent_name: Unique intent name (e.g., "borrow_book")
            description: Description of what this intent does
            trigger_phrases: List of phrases that trigger this intent
            action_type: Type of action (e.g., "open_app", "api_call")
            action_config: Action configuration (app_id, url, params, etc.)
            language: Language code
            category: Intent category

        Returns:
            IntentResponse with created intent information
        """
        # Check if intent_name already exists
        existing = db.get_intent_by_name(intent_name)
        if existing:
            raise ValueError(f"Intent with name '{intent_name}' already exists")

        # Create intent in database
        intent_entry = db.create_intent(
            intent_name=intent_name,
            description=description,
            trigger_phrases=trigger_phrases,
            action_type=action_type,
            action_config=action_config,
            language=language,
            category=category
        )

        return self._to_intent_response(intent_entry)

    def get_intent(self, intent_id: str) -> Optional[IntentResponse]:
        """Get intent by ID"""
        intent_entry = db.get_intent_by_id(intent_id)

        if intent_entry:
            return self._to_intent_response(intent_entry)
        return None

    def list_intents(self) -> List[IntentResponse]:
        """List all intents"""
        intent_entries = db.get_all_intents()
        return [self._to_intent_response(entry) for entry in intent_entries]

    def update_intent(
        self,
        intent_id: str,
        updates: Dict
    ) -> Optional[IntentResponse]:
        """
        Update intent entry

        Args:
            intent_id: Intent ID
            updates: Dictionary of fields to update

        Returns:
            Updated intent response or None if not found
        """
        # Check if updating intent_name and if it conflicts
        if 'intent_name' in updates:
            existing = db.get_intent_by_name(updates['intent_name'])
            if existing and existing.intent_id != intent_id:
                raise ValueError(f"Intent with name '{updates['intent_name']}' already exists")

        # Update in database
        intent_entry = db.update_intent(intent_id, updates)

        if intent_entry:
            return self._to_intent_response(intent_entry)
        return None

    def delete_intent(self, intent_id: str) -> bool:
        """
        Delete intent entry

        Args:
            intent_id: Intent ID

        Returns:
            True if deleted, False if not found
        """
        return db.delete_intent(intent_id)

    def _to_intent_response(self, intent_entry: IntentEntry) -> IntentResponse:
        """Convert IntentEntry to IntentResponse"""
        return IntentResponse(
            intent_id=intent_entry.intent_id,
            intent_name=intent_entry.intent_name,
            description=intent_entry.description,
            trigger_phrases=intent_entry.trigger_phrases,
            action_type=intent_entry.action_type,
            action_config=intent_entry.action_config,
            language=intent_entry.language,
            category=intent_entry.category,
            created_at=intent_entry.created_at,
            updated_at=intent_entry.updated_at
        )


# Global intent manager instance
intent_manager = IntentManager()
