"""HTTP client for calling the Docling agent (Cloud Run service)."""

import logging

import httpx

logger = logging.getLogger(__name__)

_DOCLING_TIMEOUT = 310.0  # slightly above docling agent's 300s processing timeout


def _is_localhost(url: str) -> bool:
    return "localhost" in url or "127.0.0.1" in url


def _get_id_token(audience: str) -> str:
    """Fetch a Google Cloud ID token for the given audience."""
    import google.auth.transport.requests
    import google.oauth2.id_token

    request = google.auth.transport.requests.Request()
    return google.oauth2.id_token.fetch_id_token(request, audience)


class DoclingClient:
    """Client for calling the Docling agent's /api/process-document endpoint."""

    def __init__(self, agent_url: str):
        self._agent_url = agent_url.rstrip("/")

    def _get_auth_header(self) -> dict:
        """Return Authorization header for Cloud Run; empty dict for localhost."""
        if _is_localhost(self._agent_url):
            return {}
        try:
            token = _get_id_token(self._agent_url)
            return {"Authorization": f"Bearer {token}"}
        except Exception as e:
            logger.warning("Failed to fetch ID token for docling agent: %s", e)
            return {}

    async def process_document(self, gcs_uri: str, mime_type: str, filename: str) -> dict:
        """Call docling agent to process a document from GCS.

        Args:
            gcs_uri: GCS URI of the uploaded document (gs://bucket/path).
            mime_type: MIME type of the document.
            filename: Original filename (for logging).

        Returns:
            Dict with 'content', 'metadata', and optionally 'result_gcs_uri'.

        Raises:
            RuntimeError: If docling agent returns a non-200 response.
            TimeoutError: If the request times out.
        """
        url = f"{self._agent_url}/api/process-document"
        headers = self._get_auth_header()
        payload = {
            "document_url": gcs_uri,
            "mime_type": mime_type,
            "output_format": "markdown",
        }

        logger.info(
            "Calling docling agent: url=%s, gcs_uri=%s, filename=%s",
            url,
            gcs_uri,
            filename,
        )

        try:
            async with httpx.AsyncClient(timeout=_DOCLING_TIMEOUT) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as e:
            logger.error("Docling agent timeout: filename=%s, error=%s", filename, e)
            raise TimeoutError(f"Docling agent did not respond within {_DOCLING_TIMEOUT}s") from e
        except Exception as e:
            logger.error("Docling agent request failed: filename=%s, error=%s", filename, e)
            raise RuntimeError(f"Docling agent request failed: {e}") from e

        if response.status_code != 200:
            body = response.text[:500]
            logger.error(
                "Docling agent error: status=%d, filename=%s, body=%s",
                response.status_code,
                filename,
                body,
            )
            raise RuntimeError(
                f"Docling agent returned {response.status_code}: {body}"
            )

        data = response.json()
        logger.info(
            "Docling agent success: filename=%s, content_length=%d",
            filename,
            len(data.get("content", "")),
        )
        return data
