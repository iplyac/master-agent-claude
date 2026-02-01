"""Firestore-backed session service for ADK."""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Optional

from google.adk.events import Event
from google.adk.sessions import Session
from google.adk.sessions.base_session_service import (
    BaseSessionService,
    GetSessionConfig,
    ListSessionsResponse,
)
from google.cloud import firestore

logger = logging.getLogger(__name__)

COLLECTION_NAME = "adk_sessions"
MAX_EVENTS = 100


class FirestoreSessionService(BaseSessionService):
    """ADK SessionService backed by Google Cloud Firestore."""

    def __init__(self, project_id: Optional[str] = None):
        """Initialize Firestore client.

        Args:
            project_id: GCP project ID. If None, uses default.
        """
        self._db = firestore.AsyncClient(project=project_id)
        self._collection = self._db.collection(COLLECTION_NAME)
        logger.info("FirestoreSessionService initialized")

    def _doc_id(self, app_name: str, user_id: str, session_id: str) -> str:
        """Generate Firestore document ID from session identifiers."""
        return f"{app_name}:{user_id}:{session_id}"

    def _session_to_dict(self, session: Session) -> dict[str, Any]:
        """Convert Session to Firestore document."""
        events_data = []
        for event in session.events[-MAX_EVENTS:]:
            events_data.append(event.model_dump(mode="json"))

        return {
            "id": session.id,
            "app_name": session.app_name,
            "user_id": session.user_id,
            "state": session.state,
            "events": events_data,
            "last_update_time": session.last_update_time,
            "updated_at": datetime.utcnow(),
        }

    def _dict_to_session(self, data: dict[str, Any]) -> Session:
        """Convert Firestore document to Session."""
        events = []
        for event_data in data.get("events", []):
            events.append(Event.model_validate(event_data))

        return Session(
            id=data["id"],
            app_name=data["app_name"],
            user_id=data["user_id"],
            state=data.get("state", {}),
            events=events,
            last_update_time=data.get("last_update_time", 0.0),
        )

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        """Create a new session or return existing one.

        Args:
            app_name: The name of the app.
            user_id: The id of the user.
            state: The initial state of the session.
            session_id: The client-provided session ID.

        Returns:
            The created or existing session.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        doc_id = self._doc_id(app_name, user_id, session_id)
        doc_ref = self._collection.document(doc_id)

        # Check if session exists
        doc = await doc_ref.get()
        if doc.exists:
            logger.debug("Session already exists: %s", session_id)
            return self._dict_to_session(doc.to_dict())

        # Create new session
        session = Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state or {},
            events=[],
            last_update_time=time.time(),
        )

        await doc_ref.set(self._session_to_dict(session))
        logger.info("Created new session: %s", session_id)
        return session

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        """Get a session by ID.

        Args:
            app_name: The name of the app.
            user_id: The id of the user.
            session_id: The session ID.
            config: Optional configuration for getting session.

        Returns:
            The session if found, None otherwise.
        """
        doc_id = self._doc_id(app_name, user_id, session_id)
        doc = await self._collection.document(doc_id).get()

        if not doc.exists:
            return None

        return self._dict_to_session(doc.to_dict())

    async def list_sessions(
        self, *, app_name: str, user_id: str
    ) -> ListSessionsResponse:
        """List all sessions for a user.

        Args:
            app_name: The name of the app.
            user_id: The id of the user.

        Returns:
            ListSessionsResponse with sessions (without events).
        """
        prefix = f"{app_name}:{user_id}:"
        sessions = []

        # Query documents with matching prefix
        query = self._collection.where("app_name", "==", app_name).where(
            "user_id", "==", user_id
        )

        async for doc in query.stream():
            data = doc.to_dict()
            # Return sessions without events for listing
            sessions.append(
                Session(
                    id=data["id"],
                    app_name=data["app_name"],
                    user_id=data["user_id"],
                    state={},
                    events=[],
                    last_update_time=data.get("last_update_time", 0.0),
                )
            )

        return ListSessionsResponse(sessions=sessions)

    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        """Delete a session.

        Args:
            app_name: The name of the app.
            user_id: The id of the user.
            session_id: The session ID.
        """
        doc_id = self._doc_id(app_name, user_id, session_id)
        await self._collection.document(doc_id).delete()
        logger.info("Deleted session: %s", session_id)

    async def append_event(self, session: Session, event: Event) -> Event:
        """Append an event to a session and persist to Firestore.

        Args:
            session: The session to append to.
            event: The event to append.

        Returns:
            The appended event.
        """
        # Call parent to update session state
        event = await super().append_event(session, event)

        if event.partial:
            return event

        # Persist to Firestore
        session.last_update_time = time.time()
        doc_id = self._doc_id(session.app_name, session.user_id, session.id)

        # Trim events if exceeding limit
        if len(session.events) > MAX_EVENTS:
            session.events = session.events[-MAX_EVENTS:]

        await self._collection.document(doc_id).set(self._session_to_dict(session))
        logger.debug(
            "Appended event to session: session_id=%s, events_count=%d",
            session.id,
            len(session.events),
        )
        return event

    async def close(self) -> None:
        """Close the Firestore client."""
        self._db.close()
