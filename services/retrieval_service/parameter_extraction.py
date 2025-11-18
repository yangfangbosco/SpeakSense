"""
Parameter Extraction for SpeakSense Intent System
Supports smart {slot} syntax for extracting parameters from user queries
"""
import re
from typing import Dict, List, Optional, Tuple


class ParameterExtractor:
    """Extract parameters from queries using slot-based trigger phrases"""

    def __init__(self):
        self.slot_pattern = re.compile(r'\{([^}]+)\}')

    def has_slots(self, trigger_phrase: str) -> bool:
        """Check if a trigger phrase contains slot definitions"""
        return bool(self.slot_pattern.search(trigger_phrase))

    def get_slots(self, trigger_phrase: str) -> List[str]:
        """Extract slot names from a trigger phrase

        Args:
            trigger_phrase: Trigger phrase with {slot} syntax

        Returns:
            List of slot names

        Example:
            "search {book_name} by {author}" → ["book_name", "author"]
        """
        return self.slot_pattern.findall(trigger_phrase)

    def convert_to_regex(self, trigger_phrase: str) -> str:
        """Convert trigger phrase with slots to regex pattern

        Args:
            trigger_phrase: Trigger phrase with {slot} syntax

        Returns:
            Regex pattern string

        Example:
            "search {book_name}" → "search (.+?)"
        """
        # Escape special regex characters except our slots
        escaped = re.escape(trigger_phrase)

        # Replace escaped slot markers with named groups
        # Use greedy matching (.+) to capture full content
        # \\\{slot_name\\\} → (?P<slot_name>.+)
        pattern = re.sub(
            r'\\{([^}]+)\\}',
            r'(?P<\1>.+)',
            escaped
        )

        # Add end anchor if pattern ends with a slot (ensures we match to end of string)
        if trigger_phrase.rstrip().endswith('}'):
            pattern += r'\s*$'

        # Make pattern case-insensitive and flexible with whitespace
        return pattern

    def extract_parameters(
        self,
        query: str,
        trigger_phrase: str
    ) -> Optional[Dict[str, str]]:
        """Extract parameters from query using slotted trigger phrase

        Args:
            query: User query text
            trigger_phrase: Trigger phrase with {slot} syntax

        Returns:
            Dictionary of extracted parameters, or None if no match

        Example:
            query = "search a book named Harry Potter"
            trigger = "search a book named {book_name}"
            → {"book_name": "Harry Potter"}
        """
        if not self.has_slots(trigger_phrase):
            # No slots to extract
            return {}

        # Convert trigger phrase to regex
        pattern = self.convert_to_regex(trigger_phrase)

        # Try to match
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            match = regex.search(query)

            if match:
                # Extract all named groups (slots)
                params = match.groupdict()
                # Clean up extracted values (strip whitespace)
                return {k: v.strip() for k, v in params.items()}

        except re.error as e:
            print(f"Regex error for pattern '{pattern}': {e}")

        return None

    def match_and_extract(
        self,
        query: str,
        trigger_phrases: List[str]
    ) -> Tuple[bool, Optional[str], Dict[str, str]]:
        """Try to match query against trigger phrases and extract parameters

        Args:
            query: User query text
            trigger_phrases: List of trigger phrases (may contain slots)

        Returns:
            Tuple of (matched, matched_phrase, parameters)

        Example:
            query = "find Harry Potter book"
            triggers = ["find {book_name}", "search {book_name} book"]
            → (True, "find {book_name}", {"book_name": "Harry Potter book"})
        """
        query_lower = query.lower().strip()

        for trigger in trigger_phrases:
            trigger_lower = trigger.lower().strip()

            if self.has_slots(trigger):
                # Try to extract parameters
                params = self.extract_parameters(query, trigger)
                if params is not None:
                    return True, trigger, params
            else:
                # Simple substring match (no slots)
                if trigger_lower in query_lower or query_lower in trigger_lower:
                    return True, trigger, {}

        return False, None, {}

    def validate_parameters(
        self,
        parameters: Dict[str, str],
        required_params: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """Validate that required parameters are present

        Args:
            parameters: Extracted parameters
            required_params: List of required parameter names

        Returns:
            Tuple of (valid, missing_params)
        """
        if not required_params:
            return True, []

        missing = [p for p in required_params if p not in parameters or not parameters[p]]
        return len(missing) == 0, missing


# Global extractor instance
parameter_extractor = ParameterExtractor()
