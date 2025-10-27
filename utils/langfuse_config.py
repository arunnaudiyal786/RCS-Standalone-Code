"""
LangFuse callback handler configuration and initialization

============================================================================
LANGFUSE FUNCTIONALITY TEMPORARILY DISABLED
============================================================================
All functions in this module now return None or safe defaults.
"""
import os
from typing import Optional
# LANGFUSE DISABLED - Imports commented out
# from langfuse import Langfuse
# from langfuse.langchain import CallbackHandler
# from config.settings import (
#     LANGFUSE_PUBLIC_KEY,
#     LANGFUSE_SECRET_KEY,
#     LANGFUSE_HOST,
#     LANGFUSE_ENABLED
# )


# LANGFUSE DISABLED - Function commented out
def get_langfuse_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_name: Optional[str] = None
) -> Optional[any]:
    """
    STUB FUNCTION - Langfuse disabled.

    Get configured LangFuse callback handler for tracing.

    Args:
        session_id: Optional session identifier to correlate traces with local sessions
        user_id: Optional user identifier for multi-user scenarios
        trace_name: Optional custom name for the trace

    Returns:
        None (Langfuse disabled)
    """
    # LANGFUSE DISABLED - Always return None
    return None

    # if not LANGFUSE_ENABLED:
    #     return None

    # if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
    #     print("Warning: LangFuse credentials not configured. Skipping tracing.")
    #     return None

    # try:
    #     # Set environment variables (required by CallbackHandler)
    #     os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
    #     os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
    #     os.environ["LANGFUSE_HOST"] = LANGFUSE_HOST

    #     # Initialize Langfuse client with credentials and session metadata
    #     langfuse_client = Langfuse(
    #         public_key=LANGFUSE_PUBLIC_KEY,
    #         secret_key=LANGFUSE_SECRET_KEY,
    #         host=LANGFUSE_HOST
    #     )

    #     # Create handler with just public_key (it will use the client's config)
    #     # Note: session_id, user_id, and trace_name are set at trace creation time
    #     # via the Langfuse client, not the CallbackHandler constructor
    #     handler = CallbackHandler(public_key=LANGFUSE_PUBLIC_KEY)

    #     # Store metadata for later use if needed
    #     handler._session_id = session_id
    #     handler._user_id = user_id
    #     handler._trace_name = trace_name or "langgraph_ticket_resolution"

    #     return handler
    # except Exception as e:
    #     print(f"Warning: Failed to initialize LangFuse handler: {e}")
    #     return None


# LANGFUSE DISABLED - Function commented out
def get_langfuse_config(session_id: Optional[str] = None) -> dict:
    """
    STUB FUNCTION - Langfuse disabled.

    Get LangGraph config dict with LangFuse callback handler.

    Args:
        session_id: Optional session identifier

    Returns:
        Empty dict (Langfuse disabled)
    """
    # LANGFUSE DISABLED - Always return empty dict
    return {}

    # handler = get_langfuse_handler(session_id=session_id)
    # if handler:
    #     return {"callbacks": [handler]}
    # else:
    #     return {}


# LANGFUSE DISABLED - Function commented out
def get_langfuse_client() -> Optional[any]:
    """
    STUB FUNCTION - Langfuse disabled.

    Get configured Langfuse client for prompt management and direct API access.

    Returns:
        None (Langfuse disabled)
    """
    # LANGFUSE DISABLED - Always return None
    return None

    # if not LANGFUSE_ENABLED:
    #     return None

    # if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
    #     print("Warning: LangFuse credentials not configured.")
    #     return None

    # try:
    #     client = Langfuse(
    #         public_key=LANGFUSE_PUBLIC_KEY,
    #         secret_key=LANGFUSE_SECRET_KEY,
    #         host=LANGFUSE_HOST
    #     )
    #     return client
    # except Exception as e:
    #     print(f"Warning: Failed to initialize LangFuse client: {e}")
    #     return None


# LANGFUSE DISABLED - All remaining functions commented out and stubbed

def create_prompt_in_langfuse(
    name: str,
    prompt: str,
    config: Optional[dict] = None,
    labels: Optional[list] = None
) -> bool:
    """STUB FUNCTION - Langfuse disabled. Always returns False."""
    return False


def get_prompt_from_langfuse(
    name: str,
    label: str = "production",
    version: Optional[int] = None
) -> Optional[dict]:
    """STUB FUNCTION - Langfuse disabled. Always returns None."""
    return None


def list_prompts_in_langfuse() -> Optional[list]:
    """STUB FUNCTION - Langfuse disabled. Always returns None."""
    return None


def get_prompt_versions(name: str) -> Optional[list]:
    """STUB FUNCTION - Langfuse disabled. Always returns None."""
    return None
