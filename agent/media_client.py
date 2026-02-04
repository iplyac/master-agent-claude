"""Media processing client using Vertex AI (voice transcription, image description)."""

import base64
import logging

from google import genai
from google.genai import types

from agent.config import mask_token

logger = logging.getLogger(__name__)


class MediaClient:
    """Client for processing media (audio, images) via Vertex AI."""

    def __init__(
        self,
        project: str,
        location: str,
        model_name: str,
    ):
        """Initialize the media client with Vertex AI.

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

    async def describe_image(
        self, image_base64: str, mime_type: str, session_id: str, prompt: str | None = None
    ) -> str:
        """Describe an image or answer a question about it.

        Args:
            image_base64: Base64-encoded image bytes.
            mime_type: Image MIME type (e.g., "image/jpeg").
            session_id: Session ID for logging.
            prompt: Optional question about the image.

        Returns:
            Image description or answer to the question.

        Raises:
            RuntimeError: If processing fails.
        """
        image_size = len(image_base64) * 3 // 4
        logger.info(
            "Image description request: session_id=%s, image_size=%d, mime_type=%s, has_prompt=%s",
            session_id,
            image_size,
            mime_type,
            prompt is not None,
        )

        try:
            # Build the prompt text
            if prompt:
                prompt_text = f"Look at this image and answer the following question: {prompt}"
            else:
                prompt_text = (
                    "Describe this image in detail. Include what you see, "
                    "any text visible, and relevant context."
                )

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=base64.b64decode(image_base64),
                            mime_type=mime_type,
                        ),
                        types.Part.from_text(text=prompt_text),
                    ],
                )
            ]

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
            )

            description = response.text.strip()
            logger.info(
                "Image description complete: session_id=%s, length=%d",
                session_id,
                len(description),
            )
            return description

        except Exception as e:
            error_msg = mask_token(str(e))
            logger.error("Image description error: session_id=%s, error=%s", session_id, error_msg)
            raise RuntimeError(f"Image description error: {error_msg}") from e

    async def close(self) -> None:
        """Close the client (no-op for genai client)."""
        pass
