"""Tests for FirestoreSessionService with mocked Firestore."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from tests.conftest import mock_firestore


class TestFirestoreSessionService:
    """Tests for FirestoreSessionService with mocked Firestore."""

    @pytest.fixture(autouse=True)
    def setup_mock_firestore(self):
        """Set up mock Firestore client for each test."""
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_client.collection.return_value = self.mock_collection
        mock_firestore.AsyncClient.return_value = self.mock_client
        yield

    @pytest.fixture
    def session_service(self):
        """Create a FirestoreSessionService instance."""
        # Import here to use mocked firestore
        from agent.adk_session_service import FirestoreSessionService

        return FirestoreSessionService(project_id="test-project")

    @pytest.mark.asyncio
    async def test_create_session_new(self, session_service):
        """Test creating a new session."""
        mock_doc = MagicMock()
        mock_doc.exists = False
        self.mock_collection.document.return_value.get = AsyncMock(
            return_value=mock_doc
        )
        self.mock_collection.document.return_value.set = AsyncMock()

        session = await session_service.create_session(
            app_name="master-agent",
            user_id="tg_123",
            session_id="tg_123",
        )

        assert session.id == "tg_123"
        assert session.app_name == "master-agent"
        assert session.user_id == "tg_123"
        assert session.events == []
        self.mock_collection.document.return_value.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_existing(self, session_service):
        """Test creating session when it already exists."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "id": "tg_123",
            "app_name": "master-agent",
            "user_id": "tg_123",
            "state": {},
            "events": [],
            "last_update_time": 123.0,
        }
        self.mock_collection.document.return_value.get = AsyncMock(
            return_value=mock_doc
        )

        session = await session_service.create_session(
            app_name="master-agent",
            user_id="tg_123",
            session_id="tg_123",
        )

        assert session.id == "tg_123"
        # set should not be called for existing session
        self.mock_collection.document.return_value.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_session_exists(self, session_service):
        """Test getting an existing session."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "id": "tg_123",
            "app_name": "master-agent",
            "user_id": "tg_123",
            "state": {"key": "value"},
            "events": [],
            "last_update_time": 123.0,
        }
        self.mock_collection.document.return_value.get = AsyncMock(
            return_value=mock_doc
        )

        session = await session_service.get_session(
            app_name="master-agent",
            user_id="tg_123",
            session_id="tg_123",
        )

        assert session is not None
        assert session.id == "tg_123"
        assert session.state == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_service):
        """Test getting a non-existent session."""
        mock_doc = MagicMock()
        mock_doc.exists = False
        self.mock_collection.document.return_value.get = AsyncMock(
            return_value=mock_doc
        )

        session = await session_service.get_session(
            app_name="master-agent",
            user_id="tg_123",
            session_id="nonexistent",
        )

        assert session is None

    @pytest.mark.asyncio
    async def test_delete_session(self, session_service):
        """Test deleting a session."""
        self.mock_collection.document.return_value.delete = AsyncMock()

        await session_service.delete_session(
            app_name="master-agent",
            user_id="tg_123",
            session_id="tg_123",
        )

        self.mock_collection.document.return_value.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_sessions(self, session_service):
        """Test listing sessions for a user."""
        # Create mock async iterator
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = {
            "id": "session1",
            "app_name": "master-agent",
            "user_id": "tg_123",
            "last_update_time": 123.0,
        }
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = {
            "id": "session2",
            "app_name": "master-agent",
            "user_id": "tg_123",
            "last_update_time": 456.0,
        }

        async def mock_stream():
            yield mock_doc1
            yield mock_doc2

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.stream.return_value = mock_stream()
        self.mock_collection.where.return_value = mock_query

        response = await session_service.list_sessions(
            app_name="master-agent",
            user_id="tg_123",
        )

        assert len(response.sessions) == 2
        assert response.sessions[0].id == "session1"
        assert response.sessions[1].id == "session2"

    def test_doc_id_generation(self, session_service):
        """Test document ID generation."""
        doc_id = session_service._doc_id("app", "user", "session")
        assert doc_id == "app:user:session"
