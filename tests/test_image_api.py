"""Tests for image API endpoint."""

import base64

import pytest
from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient


VALID_IMAGE_BASE64 = base64.b64encode(b"fake image data").decode()


@pytest.fixture
def mock_processor():
    """Create a mock MessageProcessor."""
    from agent.processor import MessageProcessor

    processor = MagicMock(spec=MessageProcessor)
    processor.process = AsyncMock(return_value="Hello from AI!")
    processor.process_image = AsyncMock(
        return_value={
            "response": "Test response",
            "description": "A test image",
            "processed_image_base64": None,
            "processed_image_mime_type": None,
        }
    )
    return processor


@pytest.fixture
def app_with_mocks(mock_processor):
    """Create app with mocked components."""
    from app import app

    app.state.processor = mock_processor
    return app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_image_endpoint_without_prompt(app_with_mocks, mock_processor):
    """POST /api/image without prompt returns description and null processed image fields."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/image",
            json={
                "conversation_id": "tg_123456",
                "image_base64": VALID_IMAGE_BASE64,
                "mime_type": "image/jpeg",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "description" in data
    assert data["processed_image_base64"] is None
    assert data["processed_image_mime_type"] is None
    mock_processor.process_image.assert_called_once()


@pytest.mark.asyncio
async def test_image_endpoint_with_prompt(app_with_mocks, mock_processor):
    """POST /api/image with prompt returns processed image fields."""
    mock_processor.process_image = AsyncMock(
        return_value={
            "response": "Processed response",
            "description": "Model text output",
            "processed_image_base64": "cHJvY2Vzc2VkX2ltYWdl",
            "processed_image_mime_type": "image/png",
        }
    )
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/image",
            json={
                "conversation_id": "tg_123456",
                "image_base64": VALID_IMAGE_BASE64,
                "mime_type": "image/jpeg",
                "prompt": "Remove the background",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Processed response"
    assert data["processed_image_base64"] == "cHJvY2Vzc2VkX2ltYWdl"
    assert data["processed_image_mime_type"] == "image/png"


@pytest.mark.asyncio
async def test_image_endpoint_missing_image(app_with_mocks):
    """Image endpoint without image_base64 should return 400."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/image",
            json={
                "conversation_id": "tg_123456",
                "mime_type": "image/jpeg",
            },
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_image_endpoint_unsupported_mime_type(app_with_mocks):
    """Image endpoint with unsupported mime_type should return 400."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/image",
            json={
                "conversation_id": "tg_123456",
                "image_base64": VALID_IMAGE_BASE64,
                "mime_type": "image/bmp",
            },
        )
    assert response.status_code == 400
    assert "Unsupported" in response.json().get("error", "")


@pytest.mark.asyncio
async def test_image_endpoint_invalid_base64(app_with_mocks):
    """Image endpoint with invalid base64 should return 400."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/image",
            json={
                "conversation_id": "tg_123456",
                "image_base64": "not-valid-base64!!!",
                "mime_type": "image/jpeg",
            },
        )
    assert response.status_code == 400
    assert "base64" in response.json().get("error", "").lower()


@pytest.mark.asyncio
async def test_image_endpoint_error_handling(app_with_mocks, mock_processor):
    """Image endpoint error should return 500."""
    mock_processor.process_image.side_effect = RuntimeError("Processing failed")
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/image",
            json={
                "conversation_id": "tg_123456",
                "image_base64": VALID_IMAGE_BASE64,
                "mime_type": "image/jpeg",
            },
        )
    assert response.status_code == 500
    assert "unavailable" in response.json().get("error", "").lower()
