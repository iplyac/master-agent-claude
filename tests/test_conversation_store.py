"""Tests for ConversationStore with mocked Firestore."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Import shared mock from conftest (automatically loaded)
from tests.conftest import mock_firestore

from agent.conversation_store import (
    ConversationMapping,
    ConversationStore,
    ConversationStoreError,
)


class TestConversationMapping:
    """Tests for ConversationMapping dataclass."""

    def test_to_dict(self):
        """Test conversion to Firestore document."""
        mapping = ConversationMapping(
            providers={"gemini": {"session_id": "gemini_abc123"}},
            metadata={"source": "telegram"},
        )
        result = mapping.to_dict()
        assert result["providers"] == {"gemini": {"session_id": "gemini_abc123"}}
        assert result["metadata"] == {"source": "telegram"}
        assert "created_at" in result
        assert "updated_at" in result

    def test_from_dict(self):
        """Test creation from Firestore document."""
        data = {
            "providers": {"gemini": {"session_id": "gemini_abc123"}},
            "metadata": {"source": "telegram"},
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 2),
        }
        mapping = ConversationMapping.from_dict(data)
        assert mapping.providers == {"gemini": {"session_id": "gemini_abc123"}}
        assert mapping.metadata == {"source": "telegram"}
        assert mapping.created_at == datetime(2024, 1, 1)

    def test_from_dict_empty(self):
        """Test creation from empty document."""
        mapping = ConversationMapping.from_dict({})
        assert mapping.providers == {}
        assert mapping.metadata == {}


class TestConversationStore:
    """Tests for ConversationStore with mocked Firestore."""

    @pytest.fixture(autouse=True)
    def setup_mock_firestore(self):
        """Set up mock Firestore client for each test."""
        # Create fresh mock client and collection for each test
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_client.collection.return_value = self.mock_collection
        mock_firestore.AsyncClient.return_value = self.mock_client
        yield

    @pytest.mark.asyncio
    async def test_get_existing_mapping(self):
        """Test getting an existing conversation mapping."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "providers": {"gemini": {"session_id": "gemini_abc123"}},
            "metadata": {},
        }
        self.mock_collection.document.return_value.get = AsyncMock(
            return_value=mock_doc
        )

        store = ConversationStore(project_id="test-project")
        mapping = await store.get("conv_123")

        assert mapping is not None
        assert mapping.providers["gemini"]["session_id"] == "gemini_abc123"

    @pytest.mark.asyncio
    async def test_get_nonexistent_mapping(self):
        """Test getting a non-existent conversation mapping."""
        mock_doc = MagicMock()
        mock_doc.exists = False
        self.mock_collection.document.return_value.get = AsyncMock(
            return_value=mock_doc
        )

        store = ConversationStore(project_id="test-project")
        mapping = await store.get("conv_123")

        assert mapping is None

    @pytest.mark.asyncio
    async def test_save_mapping(self):
        """Test saving a conversation mapping."""
        self.mock_collection.document.return_value.set = AsyncMock()

        store = ConversationStore(project_id="test-project")
        mapping = ConversationMapping(
            providers={"gemini": {"session_id": "gemini_abc123"}}
        )
        await store.save("conv_123", mapping)

        self.mock_collection.document.return_value.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_provider_session_existing(self):
        """Test getting existing provider session."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "providers": {"gemini": {"session_id": "gemini_existing123"}},
            "metadata": {},
        }
        self.mock_collection.document.return_value.get = AsyncMock(
            return_value=mock_doc
        )

        store = ConversationStore(project_id="test-project")
        session_id = await store.get_or_create_provider_session("conv_123", "gemini")

        assert session_id == "gemini_existing123"

    @pytest.mark.asyncio
    async def test_get_or_create_provider_session_new(self):
        """Test creating new provider session."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "providers": {},
            "metadata": {},
        }
        self.mock_collection.document.return_value.get = AsyncMock(
            return_value=mock_doc
        )
        self.mock_collection.document.return_value.set = AsyncMock()

        store = ConversationStore(project_id="test-project")
        session_id = await store.get_or_create_provider_session("conv_123", "gemini")

        assert session_id.startswith("gemini_")
        self.mock_collection.document.return_value.set.assert_called()

    @pytest.mark.asyncio
    async def test_firestore_error_handling(self):
        """Test Firestore error is wrapped in ConversationStoreError."""
        self.mock_collection.document.return_value.get = AsyncMock(
            side_effect=Exception("Firestore unavailable")
        )

        store = ConversationStore(project_id="test-project")

        with pytest.raises(ConversationStoreError) as exc_info:
            await store.get("conv_123")
        assert "unavailable" in str(exc_info.value).lower()
