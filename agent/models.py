"""Request/response models for the API."""

import logging
from typing import Optional

from pydantic import BaseModel, model_validator

logger = logging.getLogger(__name__)


class TelegramMetadata(BaseModel):
    """Telegram chat metadata."""

    chat_id: int
    user_id: int
    chat_type: str  # "private", "group", "supergroup"


class RequestMetadata(BaseModel):
    """Request metadata container."""

    telegram: Optional[TelegramMetadata] = None


class ChatRequest(BaseModel):
    """Chat API request model with backward compatibility."""

    # New format
    conversation_id: Optional[str] = None
    message: str
    metadata: Optional[RequestMetadata] = None

    # Old format (deprecated)
    session_id: Optional[str] = None

    def get_conversation_id(self) -> str:
        """Return conversation_id, falling back to session_id for backward compatibility."""
        if self.conversation_id:
            return self.conversation_id
        if self.session_id:
            logger.warning(
                "Deprecated session_id format used",
                extra={"session_id": self.session_id},
            )
            return self.session_id
        raise ValueError("Either conversation_id or session_id is required")

    @model_validator(mode="after")
    def validate_identifier(self):
        """Ensure at least one identifier is provided."""
        if not self.conversation_id and not self.session_id:
            raise ValueError("Either conversation_id or session_id is required")
        return self


class VoiceRequest(BaseModel):
    """Voice API request model with backward compatibility."""

    # New format
    conversation_id: Optional[str] = None
    audio_base64: str
    mime_type: str = "audio/ogg"
    metadata: Optional[RequestMetadata] = None

    # Old format (deprecated)
    session_id: Optional[str] = None

    def get_conversation_id(self) -> str:
        """Return conversation_id, falling back to session_id for backward compatibility."""
        if self.conversation_id:
            return self.conversation_id
        if self.session_id:
            logger.warning(
                "Deprecated session_id format used",
                extra={"session_id": self.session_id},
            )
            return self.session_id
        raise ValueError("Either conversation_id or session_id is required")

    @model_validator(mode="after")
    def validate_identifier(self):
        """Ensure at least one identifier is provided."""
        if not self.conversation_id and not self.session_id:
            raise ValueError("Either conversation_id or session_id is required")
        return self


class ChatResponse(BaseModel):
    """Chat API response model."""

    response: str


class VoiceResponse(BaseModel):
    """Voice API response model."""

    response: str
    transcription: Optional[str] = None
