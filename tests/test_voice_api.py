"""Tests for voice API endpoint."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from app import app
from agent.llm_client import LLMClient
from agent.processor import MessageProcessor


@pytest.fixture(autouse=True)
def setup_app_state():
    """Set up app.state with LLMClient and MessageProcessor for tests."""
    llm_client = LLMClient(api_key=None, model_name="gemini-2.0-flash-exp")
    processor = MessageProcessor(llm_client)
    app.state.llm_client = llm_client
    app.state.processor = processor
    yield


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_voice_endpoint_valid_contract():
    """POST /api/voice with valid data should return response and transcription."""
    with patch.object(
        app.state.processor.llm_client,
        "generate_response_from_audio",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = {
            "response": "Test response",
            "transcription": "Test transcription",
        }
        transport = ASGITransport(app=app)
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


@pytest.mark.asyncio
async def test_voice_endpoint_missing_api_key():
    """Voice endpoint with no API key should return configured error message."""
    app.state.llm_client.api_key = None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/voice",
            json={
                "session_id": "tg_123456",
                "audio_base64": "dGVzdA==",
                "mime_type": "audio/ogg",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "not configured" in data.get("response", "").lower()


@pytest.mark.asyncio
async def test_voice_endpoint_missing_audio():
    """Voice endpoint with missing audio should return 400."""
    transport = ASGITransport(app=app)
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
async def test_voice_endpoint_missing_session_id():
    """Voice endpoint with missing session_id should return 400."""
    transport = ASGITransport(app=app)
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
async def test_voice_endpoint_invalid_json():
    """Voice endpoint with invalid JSON should return 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/voice",
            content=b"not valid json",
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 400
    assert "Invalid JSON" in response.json().get("error", "")


@pytest.mark.asyncio
async def test_voice_endpoint_timeout():
    """Voice endpoint timeout should return 500."""
    with patch.object(
        app.state.processor.llm_client,
        "generate_response_from_audio",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.side_effect = RuntimeError("Timeout")
        transport = ASGITransport(app=app)
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
