"""Tests for MediaClient.summarize_document() method."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_genai_client():
    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock()
    return client


@pytest.fixture
def media_client(mock_genai_client):
    with patch("agent.media_client.genai.Client", return_value=mock_genai_client):
        from agent.media_client import MediaClient

        client = MediaClient(
            project="test-project",
            location="europe-west4",
            model_name="gemini-2.0-flash",
        )
        client.client = mock_genai_client
        return client


@pytest.mark.asyncio
async def test_summarize_document_success(media_client, mock_genai_client):
    """Returns summary text when Gemini responds successfully."""
    mock_response = MagicMock()
    mock_response.text = "  This is a financial report covering Q3 2024 results.  "
    mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    result = await media_client.summarize_document("# Q3 Report\n\nRevenue grew 12%...")

    assert result == "This is a financial report covering Q3 2024 results."
    mock_genai_client.aio.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_document_gemini_exception_returns_none(media_client, mock_genai_client):
    """Returns None (non-blocking) when Gemini raises an exception."""
    mock_genai_client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("Quota exceeded")
    )

    result = await media_client.summarize_document("# Some document content")

    assert result is None


@pytest.mark.asyncio
async def test_summarize_document_empty_content_returns_none(media_client, mock_genai_client):
    """Returns None without calling Gemini when content is empty."""
    result = await media_client.summarize_document("")

    assert result is None
    mock_genai_client.aio.models.generate_content.assert_not_called()


@pytest.mark.asyncio
async def test_summarize_document_truncates_at_30000_chars(media_client, mock_genai_client):
    """Content longer than 30 000 chars is truncated before sending to Gemini."""
    long_content = "x" * 50_000

    mock_response = MagicMock()
    mock_response.text = "A very long document."
    mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    await media_client.summarize_document(long_content)

    call_args = mock_genai_client.aio.models.generate_content.call_args
    prompt_text = call_args[1]["contents"][0].parts[0].text
    # The truncated content (30k chars) should appear in the prompt
    assert "x" * 30_000 in prompt_text
    assert "x" * 30_001 not in prompt_text


@pytest.mark.asyncio
async def test_summarize_document_empty_gemini_response_returns_none(media_client, mock_genai_client):
    """Returns None when Gemini returns an empty string."""
    mock_response = MagicMock()
    mock_response.text = "   "
    mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    result = await media_client.summarize_document("# Document")

    assert result is None
