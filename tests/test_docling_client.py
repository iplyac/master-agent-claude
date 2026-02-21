"""Tests for DoclingClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.docling_client import DoclingClient


AGENT_URL = "https://docling-agent-xxxx-ew.a.run.app"
LOCALHOST_URL = "http://localhost:8081"
GCS_URI = "gs://docling-documents/input/conv1/1700000000000_report.pdf"


@pytest.fixture
def cloud_run_client():
    return DoclingClient(AGENT_URL)


@pytest.fixture
def localhost_client():
    return DoclingClient(LOCALHOST_URL)


# --- process_document tests ---

@pytest.mark.asyncio
async def test_process_document_success(cloud_run_client):
    """Successful call returns content and metadata."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "content": "# Report\n\nContent here",
        "metadata": {"format": "markdown", "pages": 5},
    }

    with patch("agent.docling_client._get_id_token", return_value="fake-token"), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await cloud_run_client.process_document(GCS_URI, "application/pdf", "report.pdf")

    assert result["content"] == "# Report\n\nContent here"
    assert result["metadata"]["pages"] == 5


@pytest.mark.asyncio
async def test_process_document_non_200_raises_runtime_error(cloud_run_client):
    """Non-200 response raises RuntimeError."""
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable document"

    with patch("agent.docling_client._get_id_token", return_value="fake-token"), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with pytest.raises(RuntimeError, match="422"):
            await cloud_run_client.process_document(GCS_URI, "application/pdf", "report.pdf")


@pytest.mark.asyncio
async def test_process_document_timeout_raises_timeout_error(cloud_run_client):
    """Timeout raises TimeoutError."""
    import httpx

    with patch("agent.docling_client._get_id_token", return_value="fake-token"), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
        mock_client_cls.return_value = mock_client

        with pytest.raises(TimeoutError):
            await cloud_run_client.process_document(GCS_URI, "application/pdf", "report.pdf")


@pytest.mark.asyncio
async def test_localhost_url_no_authorization_header(localhost_client):
    """Localhost URL sends no Authorization header."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"content": "text", "metadata": {"format": "markdown"}}

    captured_headers = {}

    async def capture_post(url, json, headers):
        captured_headers.update(headers)
        return mock_response

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = capture_post
        mock_client_cls.return_value = mock_client

        await localhost_client.process_document(GCS_URI, "application/pdf", "report.pdf")

    assert "Authorization" not in captured_headers
