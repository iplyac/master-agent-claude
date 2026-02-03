"""Message processor using ADK Runner."""

import logging
from typing import Optional

from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService
from google.genai import types

from agent.voice_client import VoiceClient

logger = logging.getLogger(__name__)

APP_NAME = "master_agent"


class MessageProcessor:
    """Processes messages using ADK Runner."""

    def __init__(
        self,
        runner: Runner,
        session_service: BaseSessionService,
        voice_client: Optional[VoiceClient] = None,
    ):
        """Initialize the processor.

        Args:
            runner: ADK Runner for processing text messages.
            session_service: Session service for creating/managing sessions.
            voice_client: Optional client for voice message processing.
        """
        self.runner = runner
        self.session_service = session_service
        self.voice_client = voice_client

    async def process(self, conversation_id: str, message: str) -> str:
        """Process a user message and return the agent response.

        Args:
            conversation_id: Conversation identifier (used as session_id).
            message: User message text.

        Returns:
            Agent response text.

        Raises:
            RuntimeError: If processing fails.
        """
        if not message or not message.strip():
            return "Empty message received. Please send a text message."

        try:
            # Use conversation_id as both user_id and session_id
            # This ensures same Telegram chat = same session = context preserved
            user_id = conversation_id
            session_id = conversation_id

            # Ensure session exists (create if not)
            existing_session = await self.session_service.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            if existing_session is None:
                await self.session_service.create_session(
                    app_name=APP_NAME,
                    user_id=user_id,
                    session_id=session_id,
                )

            # Create content for the message
            content = types.Content(
                role="user",
                parts=[types.Part(text=message)],
            )

            logger.info(
                "Processing message: session_id=%s, message_length=%d",
                session_id,
                len(message),
            )

            # Run agent and collect final response
            response_text = None
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = event.content.parts[0].text
                    break

            if response_text is None:
                logger.warning("No final response from agent: session_id=%s", session_id)
                return "I couldn't generate a response. Please try again."

            logger.info(
                "Agent response: session_id=%s, response_length=%d",
                session_id,
                len(response_text),
            )
            return response_text

        except Exception as e:
            logger.error(
                "Processing error: conversation_id=%s, error=%s",
                conversation_id,
                e,
            )
            raise RuntimeError("Failed to process message") from e

    async def process_voice(
        self, conversation_id: str, audio_base64: str, mime_type: str
    ) -> dict:
        """Process a voice message and return transcription + response.

        Transcribes audio, then processes transcription through ADK Runner
        to maintain conversation context.

        Args:
            conversation_id: Conversation identifier.
            audio_base64: Base64-encoded audio bytes.
            mime_type: Audio MIME type.

        Returns:
            dict with "response" and "transcription" keys.

        Raises:
            RuntimeError: If processing fails.
        """
        if not audio_base64 or not audio_base64.strip():
            return {
                "response": "Empty audio received. Please send a voice message.",
                "transcription": "",
            }

        if self.voice_client is None:
            return {
                "response": "Voice processing not configured.",
                "transcription": "",
            }

        try:
            # Step 1: Transcribe audio
            transcription = await self.voice_client.transcribe(
                audio_base64, mime_type, conversation_id
            )

            if not transcription:
                return {
                    "response": "Could not transcribe the audio. Please try again.",
                    "transcription": "",
                }

            # Step 2: Process transcription through ADK Runner (preserves context)
            response = await self.process(conversation_id, transcription)

            return {
                "response": response,
                "transcription": transcription,
            }
        except RuntimeError:
            raise
        except Exception as e:
            logger.error(
                "Voice processing error: conversation_id=%s, error=%s",
                conversation_id,
                e,
            )
            raise RuntimeError("Failed to process voice message") from e
