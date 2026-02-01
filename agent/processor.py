import logging
from typing import Optional

from agent.conversation_store import ConversationStore
from agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

# Default provider name for the current LLM
DEFAULT_PROVIDER = "gemini"


class MessageProcessor:
    """Validates and delegates messages to the LLM client."""

    def __init__(
        self,
        llm_client: LLMClient,
        conversation_store: Optional[ConversationStore] = None,
    ):
        self.llm_client = llm_client
        self.conversation_store = conversation_store

    async def _get_provider_session(self, conversation_id: str) -> str:
        """Get or create provider-specific session ID for a conversation."""
        if self.conversation_store:
            return await self.conversation_store.get_or_create_provider_session(
                conversation_id, DEFAULT_PROVIDER
            )
        # Fallback: use conversation_id directly if no store configured
        return conversation_id

    async def process(self, conversation_id: str, message: str) -> str:
        """Process a user message and return the LLM response."""
        if not message or not message.strip():
            return "Empty message received. Please send a text message."

        try:
            session_id = await self._get_provider_session(conversation_id)
            return await self.llm_client.generate_response(message, session_id)
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Processing error: conversation_id=%s, error=%s", conversation_id, e)
            raise RuntimeError("Failed to process message") from e

    async def process_voice(self, conversation_id: str, audio_base64: str, mime_type: str) -> dict:
        """
        Process a voice message and return transcription + response.

        Args:
            conversation_id: Conversation identifier
            audio_base64: Base64-encoded audio bytes
            mime_type: Audio MIME type

        Returns:
            dict with "response" and "transcription" keys

        Raises:
            RuntimeError: If processing fails
        """
        if not audio_base64 or not audio_base64.strip():
            return {
                "response": "Empty audio received. Please send a voice message.",
                "transcription": "",
            }

        try:
            session_id = await self._get_provider_session(conversation_id)
            return await self.llm_client.generate_response_from_audio(
                audio_base64, mime_type, session_id
            )
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Voice processing error: conversation_id=%s, error=%s", conversation_id, e)
            raise RuntimeError("Failed to process voice message") from e
