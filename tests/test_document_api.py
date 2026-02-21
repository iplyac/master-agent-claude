"""Tests for POST /api/document endpoint."""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient


VALID_DOC_BASE64 = base64.b64encode(b"%PDF-1.4 fake pdf content").decode()
GCS_URI = "gs://docling-documents/input/conv1/1700000000000_report.pdf"


@pytest.fixture
def mock_docling_client():
    client = MagicMock()
    client.process_document = AsyncMock(
        return_value={
            "content": "# Report\n\nExtracted content",
            "metadata": {"format": "markdown", "pages": 3},
        }
    )
    return client


@pytest.fixture
def mock_docling_gcs_client():
    client = MagicMock()
    client.upload_document = AsyncMock(return_value=GCS_URI)
    return client


@pytest.fixture
def app_with_docling(mock_docling_client, mock_docling_gcs_client):
    from app import app

    app.state.docling_client = mock_docling_client
    app.state.docling_gcs_client = mock_docling_gcs_client
    return app


@pytest.fixture
def app_without_docling(mock_docling_gcs_client):
    from app import app

    app.state.docling_client = None
    app.state.docling_gcs_client = mock_docling_gcs_client
    return app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_document_endpoint_success(app_with_docling, mock_docling_client, mock_docling_gcs_client):
    """Valid request returns 200 with content and gcs_uri."""
    transport = ASGITransport(app=app_with_docling)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/document",
            json={
                "conversation_id": "tg_123456",
                "document_base64": VALID_DOC_BASE64,
                "mime_type": "application/pdf",
                "filename": "report.pdf",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert data["content"] == "# Report\n\nExtracted content"
    assert "gcs_uri" in data
    assert data["gcs_uri"] == GCS_URI
    mock_docling_gcs_client.upload_document.assert_called_once()
    mock_docling_client.process_document.assert_called_once()


@pytest.mark.asyncio
async def test_document_endpoint_missing_document_base64(app_with_docling):
    """Missing document_base64 returns 400."""
    transport = ASGITransport(app=app_with_docling)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/document",
            json={
                "conversation_id": "tg_123456",
                "mime_type": "application/pdf",
                "filename": "report.pdf",
            },
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_document_endpoint_unsupported_mime_type(app_with_docling):
    """Unsupported mime_type returns 400."""
    transport = ASGITransport(app=app_with_docling)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/document",
            json={
                "conversation_id": "tg_123456",
                "document_base64": VALID_DOC_BASE64,
                "mime_type": "audio/mpeg",
                "filename": "audio.mp3",
            },
        )
    assert response.status_code == 400
    assert "Unsupported" in response.json().get("error", "")


@pytest.mark.asyncio
async def test_document_endpoint_no_docling_url_returns_503(app_without_docling):
    """No DOCLING_AGENT_URL → 503."""
    transport = ASGITransport(app=app_without_docling)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/document",
            json={
                "conversation_id": "tg_123456",
                "document_base64": VALID_DOC_BASE64,
                "mime_type": "application/pdf",
                "filename": "report.pdf",
            },
        )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_document_endpoint_docling_agent_error_returns_502(
    app_with_docling, mock_docling_client
):
    """Docling agent RuntimeError returns 502."""
    mock_docling_client.process_document.side_effect = RuntimeError("Processing failed")
    transport = ASGITransport(app=app_with_docling)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/document",
            json={
                "conversation_id": "tg_123456",
                "document_base64": VALID_DOC_BASE64,
                "mime_type": "application/pdf",
                "filename": "report.pdf",
            },
        )
    assert response.status_code == 502


@pytest.mark.asyncio
async def test_document_endpoint_gcs_failure_returns_500_no_docling_call(
    app_with_docling, mock_docling_gcs_client, mock_docling_client
):
    """GCS upload failure returns 500 and docling agent is NOT called."""
    mock_docling_gcs_client.upload_document.side_effect = Exception("GCS permission denied")
    transport = ASGITransport(app=app_with_docling)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/document",
            json={
                "conversation_id": "tg_123456",
                "document_base64": VALID_DOC_BASE64,
                "mime_type": "application/pdf",
                "filename": "report.pdf",
            },
        )
    assert response.status_code == 500
    mock_docling_client.process_document.assert_not_called()
