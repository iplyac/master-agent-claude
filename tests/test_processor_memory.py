"""Tests for MessageProcessor memory service integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agent.processor import MessageProcessor


@pytest.fixture
def mock_runner():
    runner = MagicMock()
    return runner


@pytest.fixture
def mock_session_service():
    service = MagicMock()
    session = MagicMock()
    session.id = "server-generated-id"
    session.events = []
    # For InMemory path (no memory_service)
    service.get_session = AsyncMock(return_value=session)
    service.create_session = AsyncMock()
    # For Vertex path (with memory_service) — list_sessions returns sessions list
    sessions_response = MagicMock()
    sessions_response.sessions = [session]
    service.list_sessions = AsyncMock(return_value=sessions_response)
    return service


@pytest.fixture
def mock_memory_service():
    service = MagicMock()
    service.add_session_to_memory = AsyncMock()
    return service


def _make_final_event(text):
    event = MagicMock()
    event.is_final_response.return_value = True
    event.content = MagicMock()
    part = MagicMock()
    part.text = text
    event.content.parts = [part]
    return event


@pytest.fixture
def processor_with_memory(mock_runner, mock_session_service, mock_memory_service):
    mock_runner.run_async = MagicMock(return_value=_async_iter([_make_final_event("Response")]))
    return MessageProcessor(mock_runner, mock_session_service, memory_service=mock_memory_service)


@pytest.fixture
def processor_without_memory(mock_runner, mock_session_service):
    mock_runner.run_async = MagicMock(return_value=_async_iter([_make_final_event("Response")]))
    return MessageProcessor(mock_runner, mock_session_service)


async def _async_iter(items):
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_process_calls_add_session_to_memory(processor_with_memory, mock_memory_service, mock_session_service):
    """After successful process(), add_session_to_memory should be called."""
    await processor_with_memory.process("conv_1", "Hello")

    mock_memory_service.add_session_to_memory.assert_called_once()
    # Verify it was called with the session object
    call_args = mock_memory_service.add_session_to_memory.call_args
    assert call_args[0][0] is mock_session_service.get_session.return_value


@pytest.mark.asyncio
async def test_process_without_memory_service_works(processor_without_memory):
    """process() should work fine when memory_service is None."""
    result = await processor_without_memory.process("conv_1", "Hello")
    assert result == "Response"


@pytest.mark.asyncio
async def test_memory_error_does_not_break_process(processor_with_memory, mock_memory_service):
    """If add_session_to_memory fails, process() should still return the response."""
    mock_memory_service.add_session_to_memory.side_effect = Exception("Memory Bank error")

    result = await processor_with_memory.process("conv_1", "Hello")
    assert result == "Response"


@pytest.mark.asyncio
async def test_empty_message_skips_memory(processor_with_memory, mock_memory_service):
    """Empty messages return early without calling memory service."""
    result = await processor_with_memory.process("conv_1", "")
    assert "Empty" in result
    mock_memory_service.add_session_to_memory.assert_not_called()
