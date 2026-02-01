"""Conversation mapping storage using Firestore."""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot

logger = logging.getLogger(__name__)

COLLECTION_NAME = "conversations"


@dataclass
class ConversationMapping:
    """Represents a conversation mapping with provider sessions and history."""

    providers: dict[str, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Firestore document."""
        return {
            "providers": self.providers,
            "metadata": self.metadata,
            "history": self.history,
            "created_at": self.created_at or datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationMapping":
        """Create from Firestore document."""
        return cls(
            providers=data.get("providers", {}),
            metadata=data.get("metadata", {}),
            history=data.get("history", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class ConversationStoreError(Exception):
    """Error interacting with conversation store."""

    pass


class ConversationStore:
    """Manages conversation mappings in Firestore."""

    def __init__(self, project_id: Optional[str] = None):
        """Initialize Firestore client."""
        try:
            self._db = firestore.AsyncClient(project=project_id)
            self._collection = self._db.collection(COLLECTION_NAME)
            logger.info("ConversationStore initialized with Firestore")
        except Exception as e:
            logger.error("Failed to initialize Firestore client: %s", e)
            raise ConversationStoreError(f"Failed to initialize Firestore: {e}")

    async def get(self, conversation_id: str) -> Optional[ConversationMapping]:
        """Load conversation mapping from Firestore."""
        try:
            doc: DocumentSnapshot = await self._collection.document(
                conversation_id
            ).get()
            if doc.exists:
                return ConversationMapping.from_dict(doc.to_dict())
            return None
        except Exception as e:
            logger.error(
                "Failed to get conversation mapping: conversation_id=%s, error=%s",
                conversation_id,
                e,
            )
            raise ConversationStoreError(f"Firestore unavailable: {e}")

    async def save(
        self, conversation_id: str, mapping: ConversationMapping
    ) -> None:
        """Save conversation mapping to Firestore."""
        try:
            await self._collection.document(conversation_id).set(mapping.to_dict())
            logger.debug("Saved conversation mapping: conversation_id=%s", conversation_id)
        except Exception as e:
            logger.error(
                "Failed to save conversation mapping: conversation_id=%s, error=%s",
                conversation_id,
                e,
            )
            raise ConversationStoreError(f"Firestore unavailable: {e}")

    async def get_or_create(
        self, conversation_id: str
    ) -> ConversationMapping:
        """Get existing mapping or create a new one."""
        mapping = await self.get(conversation_id)
        if mapping is None:
            mapping = ConversationMapping()
            await self.save(conversation_id, mapping)
            logger.info("Created new conversation mapping: conversation_id=%s", conversation_id)
        return mapping

    async def get_or_create_provider_session(
        self, conversation_id: str, provider: str
    ) -> str:
        """Get or create a provider-specific session ID."""
        mapping = await self.get_or_create(conversation_id)

        if provider in mapping.providers:
            session_id = mapping.providers[provider].get("session_id")
            if session_id:
                return session_id

        # Create new session for this provider
        session_id = f"{provider}_{uuid.uuid4().hex[:12]}"
        mapping.providers[provider] = {
            "session_id": session_id,
            "created_at": datetime.utcnow(),
        }
        await self.save(conversation_id, mapping)
        logger.info(
            "Created provider session: conversation_id=%s, provider=%s, session_id=%s",
            conversation_id,
            provider,
            session_id,
        )
        return session_id

    async def update_metadata(
        self, conversation_id: str, metadata: dict[str, Any]
    ) -> None:
        """Update conversation metadata."""
        mapping = await self.get_or_create(conversation_id)
        mapping.metadata.update(metadata)
        await self.save(conversation_id, mapping)

    async def get_history(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get conversation history."""
        mapping = await self.get(conversation_id)
        if mapping:
            return mapping.history
        return []

    async def append_history(
        self, conversation_id: str, user_message: str, model_response: str
    ) -> None:
        """Append user message and model response to history."""
        mapping = await self.get_or_create(conversation_id)
        mapping.history.append({"role": "user", "parts": [{"text": user_message}]})
        mapping.history.append({"role": "model", "parts": [{"text": model_response}]})
        # Keep only last 20 turns (40 messages) to avoid token limits
        if len(mapping.history) > 40:
            mapping.history = mapping.history[-40:]
        await self.save(conversation_id, mapping)
        logger.debug(
            "Appended to history: conversation_id=%s, history_length=%d",
            conversation_id,
            len(mapping.history),
        )

    async def close(self) -> None:
        """Close the Firestore client."""
        self._db.close()
