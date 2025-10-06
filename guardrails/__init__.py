"""
Guardrails module for input validation and security checks using NeMo Guardrails.

This module provides guardrail functionality to protect the ticket resolution
system from processing sensitive or inappropriate data using NVIDIA NeMo Guardrails
with Presidio-based PII detection.
"""

from .pii_guardrails import (
    check_ticket_for_pii,
    get_enabled_pii_checks,
    GuardrailsManager
)

__all__ = [
    "check_ticket_for_pii",
    "get_enabled_pii_checks",
    "GuardrailsManager"
]
