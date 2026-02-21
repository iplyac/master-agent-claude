"""Tests for GCSStorageClient and processor GCS integration."""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.gcs_client import GCSStorageClient, _mime_to_ext
from agent.processor import MessageProcessor


# --- Unit tests for GCSStorageClient ---


@pytest.fixture
def mock_storage_client():
    """Patch google.cloud.storage.Client used inside GCSStorageClient."""
    with patch("agent.gcs_client.storage") as mock_storage:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage.Client.return_value.bucket.return_value = mock_bucket
        yield mock_storage, mock_bucket, mock_blob


@pytest.fixture
def gcs_client(mock_storage_client):
    return GCSStorageClient("test-bucket")


@pytest.mark.asyncio
async def test_upload_original_stores_in_upload_folder(gcs_client, mock_storage_client):
    """upload_original saves to upload/ folder."""
    _, mock_bucket, mock_blob = mock_storage_client
    image_bytes = b"fake image data"

    uri = await gcs_client.upload_original(image_bytes, "image/jpeg", "session-123")

    assert uri is not None
    assert uri.startswith("gs://test-bucket/upload/session-123/")
    assert uri.endswith(".jpg")
    mock_blob.upload_from_string.assert_called_once_with(image_bytes, content_type="image/jpeg")


@pytest.mark.asyncio
async def test_upload_processed_stores_in_processed_folder(gcs_client, mock_storage_client):
    """upload_processed saves to processed/ folder."""
    _, mock_bucket, mock_blob = mock_storage_client
    image_bytes = b"processed image data"

    uri = await gcs_client.upload_processed(image_bytes, "image/png", "session-456")

    assert uri is not None
    assert uri.startswith("gs://test-bucket/processed/session-456/")
    assert uri.endswith(".png")


@pytest.mark.asyncio
async def test_upload_original_gcs_error_returns_none(gcs_client, mock_storage_client):
    """GCS upload error returns None (fire-and-forget)."""
    _, _, mock_blob = mock_storage_client
    mock_blob.upload_from_string.side_effect = Exception("Permission denied")

    uri = await gcs_client.upload_original(b"data", "image/jpeg", "session-789")

    assert uri is None


@pytest.mark.parametrize("mime_type,expected_ext", [
    ("image/jpeg", "jpg"),
    ("image/jpg", "jpg"),
    ("image/png", "png"),
    ("image/gif", "gif"),
    ("image/webp", "webp"),
    ("image/bmp", "bin"),
    ("application/octet-stream", "bin"),
])
def test_mime_to_ext(mime_type, expected_ext):
    assert _mime_to_ext(mime_type) == expected_ext


# --- Processor integration tests ---

IMAGE_B64 = base64.b64encode(b"fake image").decode()
PROCESSED_B64 = base64.b64encode(b"processed image").decode()


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
    client.describe_image = AsyncMock(return_value="A cat photo")
    client.process_image_with_model = AsyncMock(
        return_value={
            "text": "Edited",
            "image_base64": PROCESSED_B64,
            "image_mime_type": "image/png",
        }
    )
    return client


@pytest.fixture
def mock_gcs_client():
    client = MagicMock()
    client.upload_original = AsyncMock(return_value="gs://bucket/upload/session/1.jpg")
    client.upload_processed = AsyncMock(return_value="gs://bucket/processed/session/1.png")
    return client


@pytest.fixture
def processor_with_gcs(mock_runner, mock_session_service, mock_media_client, mock_gcs_client):
    proc = MessageProcessor(
        mock_runner, mock_session_service, mock_media_client, gcs_client=mock_gcs_client
    )
    proc.process = AsyncMock(return_value="Agent response")
    return proc


@pytest.fixture
def processor_no_gcs(mock_runner, mock_session_service, mock_media_client):
    proc = MessageProcessor(mock_runner, mock_session_service, mock_media_client)
    proc.process = AsyncMock(return_value="Agent response")
    return proc


@pytest.mark.asyncio
async def test_original_uploaded_to_gcs_on_process_image(
    processor_with_gcs, mock_gcs_client
):
    """Original image is uploaded to upload/ when process_image is called."""
    await processor_with_gcs.process_image("conv_1", IMAGE_B64, "image/jpeg")

    mock_gcs_client.upload_original.assert_called_once()
    call_args = mock_gcs_client.upload_original.call_args
    assert call_args[0][1] == "image/jpeg"
    assert call_args[0][2] == "conv_1"


@pytest.mark.asyncio
async def test_processed_image_uploaded_to_gcs_when_model_returns_image(
    processor_with_gcs, mock_gcs_client
):
    """Processed image is uploaded to processed/ when model returns an image."""
    await processor_with_gcs.process_image(
        "conv_1", IMAGE_B64, "image/jpeg", prompt="Remove background"
    )

    mock_gcs_client.upload_processed.assert_called_once()
    call_args = mock_gcs_client.upload_processed.call_args
    assert call_args[0][1] == "image/png"
    assert call_args[0][2] == "conv_1"


@pytest.mark.asyncio
async def test_gcs_error_does_not_affect_process_image_response(
    processor_with_gcs, mock_gcs_client
):
    """GCS failure does not prevent process_image from returning a result."""
    mock_gcs_client.upload_original = AsyncMock(return_value=None)  # simulates error

    result = await processor_with_gcs.process_image("conv_1", IMAGE_B64, "image/jpeg")

    assert result["response"] == "Agent response"
    assert result["description"] == "A cat photo"


@pytest.mark.asyncio
async def test_no_gcs_client_skips_upload(processor_no_gcs, mock_media_client):
    """If gcs_client=None, no upload is attempted (backward compatibility)."""
    result = await processor_no_gcs.process_image("conv_1", IMAGE_B64, "image/jpeg")

    assert result["response"] == "Agent response"
    mock_media_client.describe_image.assert_called_once()
