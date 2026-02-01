"""Tests for voice API endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_processor():
    """Create a mock MessageProcessor."""
    from agent.processor import MessageProcessor

    processor = MagicMock(spec=MessageProcessor)
    processor.process = AsyncMock(return_value="Hello from AI!")
    processor.process_voice = AsyncMock(
        return_value={"response": "Test response", "transcription": "Test transcription"}
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
async def test_voice_endpoint_valid_contract(app_with_mocks, mock_processor):
    """POST /api/voice with valid data should return response and transcription."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/voice",
            json={
                "session_id": "tg_123456",
                "audio_base64": "dGVzdCBhdWRpbyBkYXRh",
                "mime_type": "audio/ogg",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "transcription" in data
    assert data["response"] == "Test response"
    assert data["transcription"] == "Test transcription"
    mock_processor.process_voice.assert_called_once()


@pytest.mark.asyncio
async def test_voice_endpoint_missing_audio(app_with_mocks):
    """Voice endpoint with missing audio should return 400."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/voice",
            json={
                "session_id": "tg_123456",
                "mime_type": "audio/ogg",
            },
        )
    assert response.status_code == 400
    assert "required" in response.json().get("error", "").lower()


@pytest.mark.asyncio
async def test_voice_endpoint_missing_session_id(app_with_mocks):
    """Voice endpoint with missing session_id should return 400."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/voice",
            json={
                "audio_base64": "dGVzdA==",
                "mime_type": "audio/ogg",
            },
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_voice_endpoint_invalid_json(app_with_mocks):
    """Voice endpoint with invalid JSON should return 400."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/voice",
            content=b"not valid json",
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 400
    assert "Invalid JSON" in response.json().get("error", "")


@pytest.mark.asyncio
async def test_voice_endpoint_error_handling(app_with_mocks, mock_processor):
    """Voice endpoint error should return 500."""
    mock_processor.process_voice.side_effect = RuntimeError("Processing failed")
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/voice",
            json={
                "session_id": "tg_123456",
                "audio_base64": "dGVzdA==",
                "mime_type": "audio/ogg",
            },
        )
    assert response.status_code == 500
    assert "unavailable" in response.json().get("error", "").lower()
