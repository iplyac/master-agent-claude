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
    # Cleanup not strictly needed for sync tests, but good practice


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_chat_endpoint_valid_contract():
    """POST /api/chat returns {"response": ...} with valid input."""
    with patch.object(
        app.state.processor.llm_client, "generate_response", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = "Hello from AI!"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat",
                json={"session_id": "tg_123", "message": "hello"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == "Hello from AI!"


@pytest.mark.asyncio
async def test_chat_endpoint_missing_api_key():
    """When API key is None, returns the 'not configured' fallback message."""
    app.state.llm_client.api_key = None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "tg_123", "message": "hello"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "not configured" in data["response"].lower()


@pytest.mark.asyncio
async def test_chat_endpoint_timeout():
    """Timeout from LLM results in 500 error."""
    with patch.object(
        app.state.processor.llm_client, "generate_response", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.side_effect = RuntimeError("LLM request timed out")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat",
                json={"session_id": "tg_123", "message": "hello"},
            )
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


@pytest.mark.asyncio
async def test_chat_endpoint_invalid_json():
    """Malformed request returns 400 or 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code in (400, 422)
