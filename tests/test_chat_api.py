"""Tests for chat API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_runner():
    """Create a mock ADK Runner."""
    runner = MagicMock()
    return runner


@pytest.fixture
def mock_voice_client():
    """Create a mock VoiceClient."""
    client = MagicMock()
    client.generate_response_from_audio = AsyncMock(
        return_value={"response": "Voice response", "transcription": "Hello"}
    )
    return client


@pytest.fixture
def mock_processor(mock_runner, mock_voice_client):
    """Create a mock MessageProcessor."""
    from agent.processor import MessageProcessor

    processor = MagicMock(spec=MessageProcessor)
    processor.process = AsyncMock(return_value="Hello from AI!")
    processor.process_voice = AsyncMock(
        return_value={"response": "Voice response", "transcription": "Hello"}
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
async def test_chat_endpoint_valid_contract(app_with_mocks, mock_processor):
    """POST /api/chat returns {"response": ...} with valid input."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "tg_123", "message": "hello"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "Hello from AI!"
    mock_processor.process.assert_called_once()


@pytest.mark.asyncio
async def test_chat_endpoint_with_conversation_id(app_with_mocks, mock_processor):
    """POST /api/chat with conversation_id format returns {"response": ...}."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={
                "conversation_id": "tg_dm_12345678",
                "message": "hello",
                "metadata": {
                    "telegram": {
                        "chat_id": 12345678,
                        "user_id": 12345678,
                        "chat_type": "private",
                    }
                },
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "Hello from AI!"


@pytest.mark.asyncio
async def test_chat_endpoint_missing_identifier(app_with_mocks):
    """POST /api/chat without conversation_id or session_id returns 400."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"message": "hello"},
        )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_chat_endpoint_error_handling(app_with_mocks, mock_processor):
    """Runtime error from processor results in 500 error."""
    mock_processor.process.side_effect = RuntimeError("Processing failed")
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "tg_123", "message": "hello"},
        )
    assert response.status_code == 500
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_chat_endpoint_invalid_json(app_with_mocks):
    """Malformed request returns 400."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_endpoint_empty_message(app_with_mocks, mock_processor):
    """Empty message returns special response."""
    mock_processor.process.return_value = "Empty message received. Please send a text message."
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "tg_123", "message": ""},
        )
    # Empty message should return 400 according to current implementation
    assert response.status_code == 400
