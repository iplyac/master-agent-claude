import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from agent.llm_client import LLMClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_llm_client_no_api_key():
    """LLMClient with no API key returns fallback message."""
    client = LLMClient(api_key=None, model_name="gemini-2.0-flash-exp")
    try:
        result = await client.generate_response("hello", "tg_123")
        assert "not configured" in result.lower()
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_llm_client_success():
    """LLMClient returns parsed text from successful API response."""
    test_key = "AIzaSyFakeTestKey1234567890123456789ab"
    client = LLMClient(api_key=test_key, model_name="gemini-2.0-flash-exp")
    try:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Hello! How can I help?"}]
                    }
                }
            ]
        }

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.generate_response("hi", "tg_456")

        assert result == "Hello! How can I help?"
        mock_post.assert_called_once()
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_llm_client_api_error():
    """LLMClient raises RuntimeError with masked message on API error."""
    test_key = "AIzaSyFakeTestKey1234567890123456789ab"
    client = LLMClient(api_key=test_key, model_name="gemini-2.0-flash-exp")
    try:
        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError(
            f"Server error with key {test_key}",
            request=mock_request,
            response=mock_response,
        )
        mock_response.raise_for_status.side_effect = error

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(RuntimeError) as exc_info:
                await client.generate_response("hi", "tg_789")

        # API key must be masked in the error message
        assert test_key not in str(exc_info.value)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_llm_client_voice_no_api_key():
    """Voice with no API key should return not configured message."""
    client = LLMClient(api_key=None, model_name="gemini-2.0-flash-exp")
    try:
        result = await client.generate_response_from_audio("dGVzdA==", "audio/ogg", "tg_123")
        assert result["response"] == "AI model not configured. Please contact administrator."
        assert result["transcription"] == ""
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_llm_client_voice_success():
    """Voice returns parsed transcription and response from API."""
    test_key = "AIzaSyFakeTestKey1234567890123456789ab"
    client = LLMClient(api_key=test_key, model_name="gemini-2.0-flash-exp")
    try:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "[TRANSCRIPTION]\nHello world\n[RESPONSE]\nHi there!"}]
                    }
                }
            ]
        }

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.generate_response_from_audio("dGVzdA==", "audio/ogg", "tg_456")

        assert result["transcription"] == "Hello world"
        assert result["response"] == "Hi there!"
        mock_post.assert_called_once()
    finally:
        await client.close()


def test_parse_voice_response_with_markers():
    """Parse response with [TRANSCRIPTION] and [RESPONSE] markers."""
    raw = "[TRANSCRIPTION]\nHello world\n[RESPONSE]\nHi there!"
    result = LLMClient._parse_voice_response(raw)
    assert result["transcription"] == "Hello world"
    assert result["response"] == "Hi there!"


def test_parse_voice_response_fallback():
    """Parse response without markers should use full text as response."""
    raw = "This is just a plain response"
    result = LLMClient._parse_voice_response(raw)
    assert result["transcription"] == ""
    assert result["response"] == "This is just a plain response"
