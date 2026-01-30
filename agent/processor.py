import logging

from agent.llm_client import LLMClient

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Validates and delegates messages to the LLM client."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def process(self, session_id: str, message: str) -> str:
        """Process a user message and return the LLM response."""
        if not message or not message.strip():
            return "Empty message received. Please send a text message."

        try:
            return await self.llm_client.generate_response(message, session_id)
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Processing error: session_id=%s, error=%s", session_id, e)
            raise RuntimeError("Failed to process message") from e

    async def process_voice(self, session_id: str, audio_base64: str, mime_type: str) -> dict:
        """
        Process a voice message and return transcription + response.

        Args:
            session_id: Session identifier
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
            return await self.llm_client.generate_response_from_audio(
                audio_base64, mime_type, session_id
            )
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Voice processing error: session_id=%s, error=%s", session_id, e)
            raise RuntimeError("Failed to process voice message") from e
