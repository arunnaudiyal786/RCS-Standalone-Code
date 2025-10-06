"""
Langfuse Prompt Management Integration

Provides centralized prompt management with Langfuse cloud/self-hosted instance
with fallback to local file-based prompts for reliability.
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from langfuse import Langfuse
from config.settings import (
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    LANGFUSE_HOST,
    LANGFUSE_ENABLED,
    LANGFUSE_PROMPT_MANAGEMENT_ENABLED,
    LANGFUSE_PROMPT_FALLBACK_TO_LOCAL,
    LANGFUSE_PROMPT_CACHE_TTL
)


class PromptData:
    """
    Wrapper for prompt data fetched from Langfuse or local files
    """
    def __init__(self, name: str, prompt_text: str, config: Dict[str, Any] = None, version: int = None, label: str = None):
        self.name = name
        self.prompt_text = prompt_text
        self.config = config or {}
        self.version = version
        self.label = label

    def get_langchain_prompt(self) -> str:
        """
        Get prompt text compatible with LangChain.
        Langfuse uses {{variable}}, LangChain uses {variable}
        """
        # The Langfuse SDK's get_langchain_prompt() method handles this conversion
        # For local prompts, they should already be in LangChain format
        return self.prompt_text

    def get_model_config(self, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get model configuration with fallback to defaults
        """
        return {
            "model": self.config.get("model", defaults.get("model")),
            "temperature": self.config.get("temperature", defaults.get("temperature")),
            "max_tokens": self.config.get("max_tokens", defaults.get("max_tokens"))
        }


class PromptManager:
    """
    Centralized prompt management with Langfuse integration and local fallback

    Features:
    - Fetches prompts from Langfuse with version/label support
    - Caches prompts to reduce API calls
    - Falls back to local files if Langfuse is unavailable
    - Thread-safe singleton pattern
    """

    _instance = None
    _cache: Dict[str, tuple[PromptData, datetime]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._langfuse_client = None
        self._cache = {}

        # Initialize Langfuse client if enabled
        if LANGFUSE_ENABLED and LANGFUSE_PROMPT_MANAGEMENT_ENABLED:
            try:
                self._langfuse_client = Langfuse(
                    public_key=LANGFUSE_PUBLIC_KEY,
                    secret_key=LANGFUSE_SECRET_KEY,
                    host=LANGFUSE_HOST
                )
                print("PromptManager: Langfuse client initialized successfully")
            except Exception as e:
                print(f"PromptManager: Failed to initialize Langfuse client: {e}")
                self._langfuse_client = None

    def get_prompt(self, name: str, label: str = "production", version: Optional[int] = None) -> PromptData:
        """
        Get prompt by name with specified label or version

        Args:
            name: Prompt name (e.g., "reasoning-agent")
            label: Label to fetch (default: "production")
            version: Specific version number (overrides label if provided)

        Returns:
            PromptData object containing prompt text and configuration

        Raises:
            Exception if prompt cannot be fetched from Langfuse or local file
        """
        cache_key = f"{name}:{label}:{version}"

        # Check cache first
        if cache_key in self._cache:
            cached_prompt, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=LANGFUSE_PROMPT_CACHE_TTL):
                print(f"PromptManager: Using cached prompt for '{name}' (label: {label})")
                return cached_prompt

        # Try Langfuse first if enabled
        if self._langfuse_client and LANGFUSE_PROMPT_MANAGEMENT_ENABLED:
            try:
                prompt_data = self._fetch_from_langfuse(name, label, version)
                # Cache the result
                self._cache[cache_key] = (prompt_data, datetime.now())
                print(f"PromptManager: Fetched prompt '{name}' from Langfuse (label: {label}, version: {prompt_data.version})")
                return prompt_data
            except Exception as e:
                print(f"PromptManager: Failed to fetch prompt '{name}' from Langfuse: {e}")
                if not LANGFUSE_PROMPT_FALLBACK_TO_LOCAL:
                    raise Exception(f"Failed to fetch prompt '{name}' from Langfuse and fallback is disabled") from e

        # Fallback to local file
        if LANGFUSE_PROMPT_FALLBACK_TO_LOCAL or not LANGFUSE_PROMPT_MANAGEMENT_ENABLED:
            try:
                prompt_data = self._fetch_from_local(name)
                # Cache the result
                self._cache[cache_key] = (prompt_data, datetime.now())
                print(f"PromptManager: Using local file for prompt '{name}'")
                return prompt_data
            except Exception as e:
                raise Exception(f"Failed to fetch prompt '{name}' from both Langfuse and local files") from e

        raise Exception(f"Could not fetch prompt '{name}' - all methods failed")

    def _fetch_from_langfuse(self, name: str, label: str = "production", version: Optional[int] = None) -> PromptData:
        """
        Fetch prompt from Langfuse by name and label/version
        """
        if version is not None:
            langfuse_prompt = self._langfuse_client.get_prompt(name, version=version)
        else:
            langfuse_prompt = self._langfuse_client.get_prompt(name, label=label)

        # Extract prompt text using Langfuse SDK method
        # For text prompts, use the prompt directly
        # For chat prompts, we need to format them appropriately
        if hasattr(langfuse_prompt, 'get_langchain_prompt'):
            prompt_text = langfuse_prompt.get_langchain_prompt()
        else:
            prompt_text = langfuse_prompt.prompt

        return PromptData(
            name=name,
            prompt_text=prompt_text,
            config=langfuse_prompt.config if hasattr(langfuse_prompt, 'config') else {},
            version=langfuse_prompt.version if hasattr(langfuse_prompt, 'version') else None,
            label=label
        )

    def _fetch_from_local(self, name: str) -> PromptData:
        """
        Fetch prompt from local file in prompts/ directory

        Converts prompt name from kebab-case to snake_case for file lookup
        E.g., "reasoning-agent" -> "reasoning_agent.txt"
        """
        # Convert kebab-case to snake_case and add .txt extension
        file_name = name.replace("-", "_") + ".txt"
        file_path = os.path.join("prompts", file_name)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Local prompt file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            prompt_text = f.read()

        return PromptData(
            name=name,
            prompt_text=prompt_text,
            config={},  # Local files don't have config metadata
            version=None,
            label="local"
        )

    def clear_cache(self):
        """Clear the prompt cache"""
        self._cache = {}
        print("PromptManager: Cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for debugging"""
        return {
            "cached_prompts": len(self._cache),
            "cache_keys": list(self._cache.keys()),
            "langfuse_enabled": self._langfuse_client is not None
        }


# Global instance for easy access
_prompt_manager_instance = None


def get_prompt_manager() -> PromptManager:
    """
    Get the global PromptManager instance
    """
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance
