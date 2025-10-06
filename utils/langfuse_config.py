"""
LangFuse callback handler configuration and initialization
"""
import os
from typing import Optional
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from config.settings import (
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    LANGFUSE_HOST,
    LANGFUSE_ENABLED
)


def get_langfuse_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_name: Optional[str] = None
) -> Optional[CallbackHandler]:
    """
    Get configured LangFuse callback handler for tracing.

    Args:
        session_id: Optional session identifier to correlate traces with local sessions
        user_id: Optional user identifier for multi-user scenarios
        trace_name: Optional custom name for the trace

    Returns:
        CallbackHandler instance if LangFuse is enabled and configured, None otherwise
    """
    if not LANGFUSE_ENABLED:
        return None

    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        print("Warning: LangFuse credentials not configured. Skipping tracing.")
        return None

    try:
        # Set environment variables (required by CallbackHandler)
        os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
        os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
        os.environ["LANGFUSE_HOST"] = LANGFUSE_HOST

        # Initialize Langfuse client with credentials and session metadata
        langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )

        # Create handler with just public_key (it will use the client's config)
        # Note: session_id, user_id, and trace_name are set at trace creation time
        # via the Langfuse client, not the CallbackHandler constructor
        handler = CallbackHandler(public_key=LANGFUSE_PUBLIC_KEY)

        # Store metadata for later use if needed
        handler._session_id = session_id
        handler._user_id = user_id
        handler._trace_name = trace_name or "langgraph_ticket_resolution"

        return handler
    except Exception as e:
        print(f"Warning: Failed to initialize LangFuse handler: {e}")
        return None


def get_langfuse_config(session_id: Optional[str] = None) -> dict:
    """
    Get LangGraph config dict with LangFuse callback handler.

    Args:
        session_id: Optional session identifier

    Returns:
        Config dictionary suitable for LangGraph invocations
    """
    handler = get_langfuse_handler(session_id=session_id)

    if handler:
        return {"callbacks": [handler]}
    else:
        return {}


def get_langfuse_client() -> Optional[Langfuse]:
    """
    Get configured Langfuse client for prompt management and direct API access.

    Returns:
        Langfuse client instance if enabled and configured, None otherwise
    """
    if not LANGFUSE_ENABLED:
        return None

    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        print("Warning: LangFuse credentials not configured.")
        return None

    try:
        client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )
        return client
    except Exception as e:
        print(f"Warning: Failed to initialize LangFuse client: {e}")
        return None


def create_prompt_in_langfuse(
    name: str,
    prompt: str,
    config: Optional[dict] = None,
    labels: Optional[list] = None
) -> bool:
    """
    Create or update a prompt in Langfuse.

    Args:
        name: Prompt name (e.g., "reasoning-agent")
        prompt: Prompt text content
        config: Optional configuration dict (model settings, etc.)
        labels: Optional list of labels (e.g., ["production", "v1.0"])

    Returns:
        True if successful, False otherwise
    """
    client = get_langfuse_client()
    if not client:
        print("Cannot create prompt: LangFuse client not available")
        return False

    try:
        client.create_prompt(
            name=name,
            prompt=prompt,
            config=config or {},
            labels=labels or ["production"]
        )
        print(f"Successfully created/updated prompt '{name}' in Langfuse")
        return True
    except Exception as e:
        print(f"Failed to create prompt '{name}' in Langfuse: {e}")
        return False


def get_prompt_from_langfuse(
    name: str,
    label: str = "production",
    version: Optional[int] = None
) -> Optional[dict]:
    """
    Fetch a prompt from Langfuse.

    Args:
        name: Prompt name (e.g., "reasoning-agent")
        label: Label to fetch (default: "production")
        version: Specific version number (overrides label if provided)

    Returns:
        Dictionary with prompt data or None if not found
        {
            "name": str,
            "prompt": str,
            "version": int,
            "config": dict,
            "labels": list
        }
    """
    client = get_langfuse_client()
    if not client:
        print("Cannot fetch prompt: LangFuse client not available")
        return None

    try:
        if version is not None:
            langfuse_prompt = client.get_prompt(name, version=version)
        else:
            langfuse_prompt = client.get_prompt(name, label=label)

        # Extract prompt text
        if hasattr(langfuse_prompt, 'get_langchain_prompt'):
            prompt_text = langfuse_prompt.get_langchain_prompt()
        else:
            prompt_text = langfuse_prompt.prompt

        return {
            "name": name,
            "prompt": prompt_text,
            "version": langfuse_prompt.version if hasattr(langfuse_prompt, 'version') else None,
            "config": langfuse_prompt.config if hasattr(langfuse_prompt, 'config') else {},
            "labels": langfuse_prompt.labels if hasattr(langfuse_prompt, 'labels') else []
        }
    except Exception as e:
        print(f"Failed to fetch prompt '{name}' from Langfuse: {e}")
        return None


def list_prompts_in_langfuse() -> Optional[list]:
    """
    List all available prompts in Langfuse.

    Returns:
        List of prompt names or None if failed
    """
    client = get_langfuse_client()
    if not client:
        print("Cannot list prompts: LangFuse client not available")
        return None

    try:
        # Note: Langfuse SDK may not have a direct list_prompts method
        # This is a placeholder - actual implementation depends on SDK capabilities
        # You may need to use the REST API directly or track prompts separately
        print("Warning: list_prompts_in_langfuse() requires manual tracking or REST API usage")
        return []
    except Exception as e:
        print(f"Failed to list prompts from Langfuse: {e}")
        return None


def get_prompt_versions(name: str) -> Optional[list]:
    """
    Get version history for a prompt in Langfuse.

    Args:
        name: Prompt name

    Returns:
        List of version numbers or None if failed
    """
    client = get_langfuse_client()
    if not client:
        print("Cannot get prompt versions: LangFuse client not available")
        return None

    try:
        # Note: Langfuse SDK may not have a direct get_versions method
        # This is a placeholder - actual implementation depends on SDK capabilities
        # You may need to use the REST API directly
        print("Warning: get_prompt_versions() requires manual tracking or REST API usage")
        return []
    except Exception as e:
        print(f"Failed to get versions for prompt '{name}' from Langfuse: {e}")
        return None
