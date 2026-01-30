import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def get_secret(
    project_id: str,
    secret_id: str = "GOOGLE_API_KEY",
    version: str = "latest",
) -> Optional[str]:
    """Fetch a secret from Google Secret Manager."""
    if not project_id:
        logger.debug("No project_id provided, skipping Secret Manager lookup")
        return None

    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        logger.info("Secret '%s' fetched from Secret Manager", secret_id)
        return payload
    except Exception as e:
        logger.warning("Failed to fetch secret '%s': %s", secret_id, type(e).__name__)
        return None


def extract_api_key(payload: str) -> Optional[str]:
    """
    Extract API key from various secret formats.

    Supported formats:
    1. Plain key string (e.g. "AIzaSy...")
    2. KEY=VALUE format (e.g. "MODEL_API_KEY=AIzaSy...")
    3. Concatenated key=value pairs without newlines
    """
    if not payload:
        return None

    # Try KEY=VALUE pattern: MODEL_API_KEY=<value>
    match = re.search(r"MODEL_API_KEY=(\S+)", payload)
    if match:
        return match.group(1)

    # Try generic KEY=VALUE where value looks like a Gemini API key
    match = re.search(r"(?:^|[\s;])([A-Za-z0-9_-]{30,})", payload)
    if match:
        return match.group(1)

    # Fallback: return stripped payload if it looks like a key
    stripped = payload.strip()
    if stripped and not stripped.isspace():
        return stripped

    return None
