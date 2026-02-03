"""Voice message transcription client using Vertex AI."""

import base64
import logging

from google import genai
from google.genai import types

from agent.config import mask_token

logger = logging.getLogger(__name__)


class VoiceClient:
    """Client for transcribing voice messages via Vertex AI."""

    def __init__(
        self,
        project: str,
        location: str,
        model_name: str,
    ):
        """Initialize the voice client with Vertex AI.

        Args:
            project: GCP project ID.
            location: GCP location (e.g., europe-west4).
            model_name: Model name to use.
        """
        self.project = project
        self.location = location
        self.model_name = model_name
        self.client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

    async def transcribe(self, audio_base64: str, mime_type: str, session_id: str) -> str:
        """Transcribe audio to text.

        Args:
            audio_base64: Base64-encoded audio bytes.
            mime_type: Audio MIME type (e.g., "audio/ogg").
            session_id: Session ID for logging.

        Returns:
            Transcribed text.

        Raises:
            RuntimeError: If transcription fails.
        """
        audio_size = len(audio_base64) * 3 // 4
        logger.info(
            "Transcription request: session_id=%s, audio_size=%d, mime_type=%s",
            session_id,
            audio_size,
            mime_type,
        )

        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=base64.b64decode(audio_base64),
                            mime_type=mime_type,
                        ),
                        types.Part.from_text(
                            text="Transcribe this audio message exactly as spoken. "
                            "Output ONLY the transcription, nothing else."
                        ),
                    ],
                )
            ]

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
            )

            transcription = response.text.strip()
            logger.info(
                "Transcription complete: session_id=%s, length=%d",
                session_id,
                len(transcription),
            )
            return transcription

        except Exception as e:
            error_msg = mask_token(str(e))
            logger.error("Transcription error: session_id=%s, error=%s", session_id, error_msg)
            raise RuntimeError(f"Transcription error: {error_msg}") from e

    async def close(self) -> None:
        """Close the client (no-op for genai client)."""
        pass
