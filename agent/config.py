import logging
import os
import re
from typing import Optional

from secret_manager import extract_api_key, get_secret

logger = logging.getLogger(__name__)


def sanitize_value(value: Optional[str]) -> Optional[str]:
    """Remove whitespace and control characters from a value."""
    if not value:
        return value
    value = value.strip()
    value = re.sub(r"[\x00-\x1f\x7f]", "", value)
    if not value:
        return None
    return value


def mask_token(message: str) -> str:
    """Mask API keys that appear in error messages."""
    # Mask Gemini-style keys (AIza... ~39 chars total)
    masked = re.sub(r"AIza[A-Za-z0-9_-]{20,}", "AIza***MASKED***", message)
    # Mask generic long tokens (30+ alphanumeric chars)
    masked = re.sub(r"[A-Za-z0-9_-]{30,}", "***MASKED***", masked)
    return masked


def get_port() -> int:
    """Return configured port or default 8080."""
    try:
        return int(os.getenv("PORT", "8080"))
    except (ValueError, TypeError):
        return 8080


def get_project_id() -> str:
    """Return GCP project ID from environment."""
    return os.getenv("GCP_PROJECT_ID") or os.getenv("PROJECT_ID") or ""


def get_model_api_key() -> Optional[str]:
    """
    Resolve model API key.

    Resolution order:
    1. MODEL_API_KEY env var -> extract + sanitize
    2. Secret Manager (secret_id from env or default "GOOGLE_API_KEY") -> extract + sanitize
    3. Return None (service starts without key)
    """
    # 1) Check env var
    key_env = os.getenv("MODEL_API_KEY")
    if key_env:
        key = extract_api_key(key_env)
        if key:
            sanitized = sanitize_value(key)
            if sanitized:
                logger.info("API key resolved from MODEL_API_KEY env var")
                return sanitized

    # 2) Try Secret Manager
    project_id = get_project_id()
    secret_id = os.getenv("MODEL_API_KEY_SECRET_ID", "GOOGLE_API_KEY")
    payload = get_secret(project_id, secret_id)
    if payload:
        key = extract_api_key(payload)
        if key:
            sanitized = sanitize_value(key)
            if sanitized:
                logger.info("API key resolved from Secret Manager")
                return sanitized

    # 3) No key available
    logger.warning("No MODEL_API_KEY configured; agent will respond with fallback message")
    return None


def get_model_name() -> str:
    """Return model name or default."""
    return os.getenv("MODEL_NAME") or "gemini-2.0-flash"


def get_model_endpoint() -> Optional[str]:
    """Return custom model endpoint if set."""
    return os.getenv("MODEL_ENDPOINT") or None


def get_log_level() -> str:
    """Return log level or default INFO."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_region() -> str:
    """Return deployment region."""
    return os.getenv("REGION") or "europe-west4"


def get_location() -> str:
    """Return GCP location for Vertex AI."""
    return os.getenv("GCP_LOCATION") or os.getenv("REGION") or "europe-west4"


def get_service_name() -> str:
    """Return service name."""
    return os.getenv("SERVICE_NAME") or "ai-agent"


def get_prompt_id() -> Optional[str]:
    """Return Vertex AI Prompt ID if configured."""
    return os.getenv("AGENT_PROMPT_ID") or None
