"""Tests for MediaClient.process_image_with_model() method."""

import base64

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_genai_client():
    """Create a mock genai client."""
    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock()
    return client


@pytest.fixture
def media_client(mock_genai_client):
    """Create a MediaClient with mocked genai client."""
    with patch("agent.media_client.genai.Client", return_value=mock_genai_client):
        from agent.media_client import MediaClient

        client = MediaClient(
            project="test-project",
            location="europe-west4",
            model_name="gemini-2.0-flash",
            image_model_name="gemini-3-pro-image-preview",
        )
    client.client = mock_genai_client
    return client


def _make_text_part(text):
    part = MagicMock()
    part.text = text
    part.inline_data = None
    return part


def _make_image_part(data: bytes, mime_type: str):
    part = MagicMock()
    part.text = None
    part.inline_data = MagicMock()
    part.inline_data.data = data
    part.inline_data.mime_type = mime_type
    return part


def _make_response(parts):
    response = MagicMock()
    content = MagicMock()
    content.parts = parts
    candidate = MagicMock()
    candidate.content = content
    response.candidates = [candidate]
    return response


IMAGE_BASE64 = base64.b64encode(b"fake image").decode()


@pytest.mark.asyncio
async def test_process_image_with_model_text_and_image(media_client, mock_genai_client):
    """Model returns both text and image."""
    image_data = b"processed image bytes"
    response = _make_response([
        _make_text_part("Here is your edited image"),
        _make_image_part(image_data, "image/png"),
    ])
    mock_genai_client.aio.models.generate_content.return_value = response

    result = await media_client.process_image_with_model(
        IMAGE_BASE64, "image/jpeg", "session_1", "Remove background"
    )

    assert result["text"] == "Here is your edited image"
    assert result["image_base64"] == base64.b64encode(image_data).decode("utf-8")
    assert result["image_mime_type"] == "image/png"
    mock_genai_client.aio.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_process_image_with_model_text_only(media_client, mock_genai_client):
    """Model returns only text, no image."""
    response = _make_response([_make_text_part("I cannot process this image.")])
    mock_genai_client.aio.models.generate_content.return_value = response

    result = await media_client.process_image_with_model(
        IMAGE_BASE64, "image/jpeg", "session_1", "Do something"
    )

    assert result["text"] == "I cannot process this image."
    assert result["image_base64"] is None
    assert result["image_mime_type"] is None


@pytest.mark.asyncio
async def test_process_image_with_model_error(media_client, mock_genai_client):
    """Model call raises an exception."""
    mock_genai_client.aio.models.generate_content.side_effect = Exception("API error")

    with pytest.raises(RuntimeError, match="Image model processing error"):
        await media_client.process_image_with_model(
            IMAGE_BASE64, "image/jpeg", "session_1", "Edit this"
        )


@pytest.mark.asyncio
async def test_process_image_with_model_uses_image_model(media_client, mock_genai_client):
    """Verify the image model name is used, not the default text model."""
    response = _make_response([_make_text_part("Done")])
    mock_genai_client.aio.models.generate_content.return_value = response

    await media_client.process_image_with_model(
        IMAGE_BASE64, "image/jpeg", "session_1", "Test prompt"
    )

    call_kwargs = mock_genai_client.aio.models.generate_content.call_args
    assert call_kwargs.kwargs["model"] == "gemini-3-pro-image-preview"
