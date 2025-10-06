import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables with defaults
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))

# LangFuse Configuration for observability and tracing
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"

# LangFuse Prompt Management Configuration
LANGFUSE_PROMPT_MANAGEMENT_ENABLED = os.getenv("LANGFUSE_PROMPT_MANAGEMENT_ENABLED", "true").lower() == "true"
LANGFUSE_PROMPT_FALLBACK_TO_LOCAL = os.getenv("LANGFUSE_PROMPT_FALLBACK_TO_LOCAL", "true").lower() == "true"
LANGFUSE_PROMPT_CACHE_TTL = int(os.getenv("LANGFUSE_PROMPT_CACHE_TTL", "300"))  # Cache TTL in seconds

# LangFuse Prompt Sync Configuration
LANGFUSE_PROMPT_SYNC_METADATA_FILE = os.getenv("LANGFUSE_PROMPT_SYNC_METADATA_FILE", "prompts/.prompt_metadata.json")
LANGFUSE_PROMPT_SYNC_AUTO_RESOLVE = os.getenv("LANGFUSE_PROMPT_SYNC_AUTO_RESOLVE", "false").lower() == "true"
LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL = os.getenv("LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL", "production")