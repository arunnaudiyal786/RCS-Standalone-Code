"""
NeMo Guardrails integration for PII detection.

============================================================================
PII GUARDRAILS FUNCTIONALITY TEMPORARILY DISABLED
============================================================================
This module provides stub functions that always return "no PII found".
All NeMo Guardrails integration is commented out.
"""

import os
from typing import Optional
from pathlib import Path
from datetime import datetime
# GUARDRAILS DISABLED - Imports commented out
# from nemoguardrails import RailsConfig, LLMRails
# from config.settings import OPENAI_API_KEY
from models.data_models import PIIDetectionResult, PIIDetectionItem


# GUARDRAILS DISABLED - Class commented out
# class GuardrailsManager:
#     """
#     Manager for NeMo Guardrails PII detection.
#
#     Uses LLM-based PII detection to identify sensitive information
#     in ticket descriptions before processing.
#     """
#
#     _instance: Optional['GuardrailsManager'] = None
#     _rails: Optional[LLMRails] = None
#
#     def __init__(self):
#         """Initialize guardrails from config directory."""
#         if GuardrailsManager._rails is None:
#             config_path = Path(__file__).parent
#
#             # Set OpenAI API key for NeMo Guardrails
#             os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
#
#             try:
#                 # Load configuration from guardrails folder
#                 config = RailsConfig.from_path(str(config_path))
#                 GuardrailsManager._rails = LLMRails(config)
#                 print(f"NeMo Guardrails initialized from: {config_path}")
#             except Exception as e:
#                 print(f"Warning: Failed to initialize NeMo Guardrails: {e}")
#                 print(f"   Config path: {config_path}")
#                 raise
#
#     @classmethod
#     def get_instance(cls) -> 'GuardrailsManager':
#         """Get or create singleton instance."""
#         if cls._instance is None:
#             cls._instance = GuardrailsManager()
#         return cls._instance
#
#     def check_pii(self, text: str, session_id: str = "unknown") -> PIIDetectionResult:
#         """
#         Check text for PII using NeMo Guardrails with LLM-based detection.
#
#         Args:
#             text: Ticket description to check
#             session_id: Session identifier for tracking
#
#         Returns:
#             PIIDetectionResult with detection details
#         """
#         if not text or not text.strip():
#             return self._create_empty_result(session_id, text)
#
#         try:
#             # Generate with guardrails - will use LLM to check for PII
#             response = self._rails.generate(
#                 messages=[{
#                     "role": "user",
#                     "content": text
#                 }]
#             )
#
#             # Check if guardrails blocked/refused the message
#             # NeMo Guardrails returns a refusal message when PII is detected
#             response_content = ""
#             if isinstance(response, dict):
#                 response_content = response.get("content", "")
#             elif hasattr(response, 'content'):
#                 response_content = response.content
#             else:
#                 response_content = str(response)
#
#             response_lower = response_content.lower()
#
#             # Check for refusal indicators
#             pii_detected = any(keyword in response_lower for keyword in [
#                 "cannot process",
#                 "contains personally identifiable information",
#                 "contains pii",
#                 "remove any personal information",
#                 "personally identifiable information",
#                 "refuse to process"
#             ])
#
#             if pii_detected:
#                 # PII was detected - extract what types if possible
#                 pii_types = self._extract_pii_types_from_response(response_content)
#
#                 return PIIDetectionResult(
#                     pii_found=True,
#                     pii_types=pii_types if pii_types else ["PII_DETECTED"],
#                     pii_count=len(pii_types) if pii_types else 1,
#                     detection_details=[],
#                     ticket_excerpt=self._create_excerpt(text),
#                     session_id=session_id,
#                     timestamp=datetime.now().isoformat()
#                 )
#
#             # No PII detected - guardrails allowed the message through
#             return self._create_empty_result(session_id, text)
#
#         except Exception as e:
#             # If guardrails throw exception, check if it's PII-related
#             error_msg = str(e).lower()
#
#             if any(keyword in error_msg for keyword in [
#                 "pii", "personal", "sensitive", "refuse", "block"
#             ]):
#                 # This is likely a PII detection
#                 pii_types = self._extract_pii_types_from_error(str(e))
#
#                 return PIIDetectionResult(
#                     pii_found=True,
#                     pii_types=pii_types if pii_types else ["PII_DETECTED"],
#                     pii_count=len(pii_types) if pii_types else 1,
#                     detection_details=[],
#                     ticket_excerpt=self._create_excerpt(text),
#                     session_id=session_id,
#                     timestamp=datetime.now().isoformat()
#                 )
#             else:
#                 # Different error - re-raise
#                 print(f"Guardrails error: {e}")
#                 raise
#
#     def _extract_pii_types_from_response(self, response_content: str) -> list:
#         """Extract PII types mentioned in the response."""
#         pii_types = []
#         response_upper = response_content.upper()
#
#         # Common PII types to look for
#         pii_keywords = {
#             "NAME": "PERSON",
#             "EMAIL": "EMAIL_ADDRESS",
#             "PHONE": "PHONE_NUMBER",
#             "ADDRESS": "LOCATION",
#             "SOCIAL SECURITY": "US_SSN",
#             "CREDIT CARD": "CREDIT_CARD",
#             "IP ADDRESS": "IP_ADDRESS"
#         }
#
#         for keyword, pii_type in pii_keywords.items():
#             if keyword in response_upper:
#                 pii_types.append(pii_type)
#
#         return pii_types if pii_types else ["PII_DETECTED"]
#
#     def _create_excerpt(self, text: str, max_length: int = 150) -> str:
#         """Create safe excerpt of text."""
#         if len(text) <= max_length:
#             return text
#         return text[:max_length] + "..."
#
#     def _create_empty_result(self, session_id: str, text: str) -> PIIDetectionResult:
#         """Create result for no PII found."""
#         return PIIDetectionResult(
#             pii_found=False,
#             pii_types=[],
#             pii_count=0,
#             detection_details=[],
#             ticket_excerpt=text if text else "",
#             session_id=session_id,
#             timestamp=datetime.now().isoformat()
#         )
#
#     def _extract_pii_types_from_error(self, error_msg: str) -> list:
#         """Extract PII entity types from error message."""
#         known_entities = [
#             "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
#             "US_SSN", "IP_ADDRESS", "LOCATION", "DATE_TIME"
#         ]
#
#         found_types = []
#         error_upper = error_msg.upper()
#
#         for entity in known_entities:
#             if entity in error_upper:
#                 found_types.append(entity)
#
#         return found_types


# STUB CLASS - Guardrails disabled
class GuardrailsManager:
    """STUB CLASS - Guardrails disabled. Always returns no PII found."""

    _instance: Optional['GuardrailsManager'] = None

    def __init__(self):
        """Stub init - does nothing."""
        pass

    @classmethod
    def get_instance(cls) -> 'GuardrailsManager':
        """Get or create stub singleton instance."""
        if cls._instance is None:
            cls._instance = GuardrailsManager()
        return cls._instance

    def check_pii(self, text: str, session_id: str = "unknown") -> PIIDetectionResult:
        """STUB - Always returns no PII found."""
        return PIIDetectionResult(
            pii_found=False,
            pii_types=[],
            pii_count=0,
            detection_details=[],
            ticket_excerpt=text[:150] if text else "",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )


# Public API functions (stub implementations)

def check_ticket_for_pii(ticket_text: str, session_id: str = "unknown") -> PIIDetectionResult:
    """
    STUB FUNCTION - Guardrails disabled.

    Check a ticket for PII using NeMo Guardrails.

    This is the main function to be imported in nodes.py.

    Args:
        ticket_text: Ticket description to check
        session_id: Session ID for tracking

    Returns:
        PIIDetectionResult with detection status (always no PII found)
    """
    # GUARDRAILS DISABLED - Always return no PII found
    return PIIDetectionResult(
        pii_found=False,
        pii_types=[],
        pii_count=0,
        detection_details=[],
        ticket_excerpt=ticket_text[:150] if ticket_text else "",
        session_id=session_id,
        timestamp=datetime.now().isoformat()
    )


def get_enabled_pii_checks() -> list:
    """
    STUB FUNCTION - Guardrails disabled.

    Get list of PII types that are checked.

    Returns:
        Empty list (guardrails disabled)
    """
    # GUARDRAILS DISABLED - Return empty list
    return []
