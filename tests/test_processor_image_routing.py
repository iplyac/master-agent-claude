"""Tests for MessageProcessor.process_image() routing logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.processor import MessageProcessor


@pytest.fixture
def mock_runner():
    runner = MagicMock()
    return runner


@pytest.fixture
def mock_session_service():
    service = MagicMock()
    service.get_session = AsyncMock(return_value=MagicMock())
    return service


@pytest.fixture
def mock_media_client():
    client = MagicMock()
    client.describe_image = AsyncMock(return_value="A photo of a cat")
    client.process_image_with_model = AsyncMock(
        return_value={
            "text": "Here is the edited image",
            "image_base64": "cHJvY2Vzc2VkX2ltYWdl",
            "image_mime_type": "image/png",
        }
    )
    return client


@pytest.fixture
def processor(mock_runner, mock_session_service, mock_media_client):
    proc = MessageProcessor(mock_runner, mock_session_service, mock_media_client)
    proc.process = AsyncMock(return_value="Agent response")
    return proc


IMAGE_BASE64 = "ZmFrZWltYWdl"


@pytest.mark.asyncio
async def test_image_with_prompt_routes_to_model(processor, mock_media_client):
    """Image + prompt should call process_image_with_model, not describe_image."""
    result = await processor.process_image(
        "conv_1", IMAGE_BASE64, "image/jpeg", prompt="Remove background"
    )

    mock_media_client.process_image_with_model.assert_called_once_with(
        IMAGE_BASE64, "image/jpeg", "conv_1", "Remove background"
    )
    mock_media_client.describe_image.assert_not_called()
    assert result["processed_image_base64"] == "cHJvY2Vzc2VkX2ltYWdl"
    assert result["processed_image_mime_type"] == "image/png"


@pytest.mark.asyncio
async def test_image_without_prompt_routes_to_describe(processor, mock_media_client):
    """Image without prompt should call describe_image, not process_image_with_model."""
    result = await processor.process_image(
        "conv_1", IMAGE_BASE64, "image/jpeg", prompt=None
    )

    mock_media_client.describe_image.assert_called_once_with(
        IMAGE_BASE64, "image/jpeg", "conv_1"
    )
    mock_media_client.process_image_with_model.assert_not_called()
    assert result["processed_image_base64"] is None
    assert result["processed_image_mime_type"] is None


@pytest.mark.asyncio
async def test_image_without_prompt_returns_description(processor, mock_media_client):
    """Image without prompt should include the description."""
    result = await processor.process_image(
        "conv_1", IMAGE_BASE64, "image/jpeg", prompt=None
    )

    assert result["description"] == "A photo of a cat"
    assert result["response"] == "Agent response"


@pytest.mark.asyncio
async def test_image_with_prompt_returns_model_text_as_description(processor, mock_media_client):
    """Image with prompt should use model text output as description."""
    result = await processor.process_image(
        "conv_1", IMAGE_BASE64, "image/jpeg", prompt="Edit this"
    )

    assert result["description"] == "Here is the edited image"
    assert result["response"] == "Agent response"


@pytest.mark.asyncio
async def test_empty_image_returns_all_fields(processor):
    """Empty image should return all fields including new ones."""
    result = await processor.process_image("conv_1", "", "image/jpeg")

    assert "processed_image_base64" in result
    assert "processed_image_mime_type" in result
    assert result["processed_image_base64"] is None
    assert result["processed_image_mime_type"] is None
