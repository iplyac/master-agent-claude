import logging
from typing import Optional

import httpx

from agent.config import mask_token

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"


class LLMClient:
    """Client for calling Gemini (or compatible) LLM API via httpx."""

    def __init__(
        self,
        api_key: Optional[str],
        model_name: str,
        endpoint: Optional[str] = None,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        self.client = httpx.AsyncClient(timeout=25.0)

    async def generate_response(self, message: str, session_id: str) -> str:
        """Send message to LLM and return text response."""
        if self.api_key is None:
            return "AI model not configured. Please contact administrator."

        url = f"{self.endpoint}/{self.model_name}:generateContent"
        params = {"key": self.api_key}
        body = {
            "contents": [{"parts": [{"text": message}]}],
        }

        logger.info(
            "LLM request: session_id=%s, message_length=%d, model=%s",
            session_id,
            len(message),
            self.model_name,
        )

        try:
            response = await self.client.post(
                url,
                params=params,
                json=body,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            text = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(
                "LLM response: session_id=%s, response_length=%d",
                session_id,
                len(text),
            )
            return text

        except httpx.TimeoutException as e:
            error_msg = mask_token(str(e))
            logger.error("LLM timeout: session_id=%s, error=%s", session_id, error_msg)
            raise RuntimeError(f"LLM request timed out: {error_msg}") from e
        except httpx.HTTPStatusError as e:
            error_msg = mask_token(str(e))
            logger.error(
                "LLM HTTP error: session_id=%s, status=%d, error=%s",
                session_id,
                e.response.status_code,
                error_msg,
            )
            raise RuntimeError(f"LLM API error: {error_msg}") from e
        except Exception as e:
            error_msg = mask_token(str(e))
            logger.error("LLM error: session_id=%s, error=%s", session_id, error_msg)
            raise RuntimeError(f"LLM error: {error_msg}") from e

    async def generate_response_from_audio(
        self, audio_base64: str, mime_type: str, session_id: str
    ) -> dict:
        """
        Send audio to Gemini multimodal API for transcription + response.

        Args:
            audio_base64: Base64-encoded audio bytes
            mime_type: Audio MIME type (e.g., "audio/ogg")
            session_id: Session ID for logging

        Returns:
            dict with keys: "response", "transcription"
        """
        if self.api_key is None:
            return {
                "response": "AI model not configured. Please contact administrator.",
                "transcription": "",
            }

        url = f"{self.endpoint}/{self.model_name}:generateContent"
        params = {"key": self.api_key}
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": audio_base64,
                            }
                        },
                        {
                            "text": (
                                "You received a voice message. "
                                "First, transcribe the audio exactly as spoken. "
                                "Then, respond to the content naturally.\n\n"
                                "Format your reply EXACTLY as:\n"
                                "[TRANSCRIPTION]\n<exact transcription>\n"
                                "[RESPONSE]\n<your response>"
                            ),
                        },
                    ]
                }
            ],
        }

        audio_size = len(audio_base64) * 3 // 4  # approximate decoded size
        logger.info(
            "LLM voice request: session_id=%s, audio_size=%d, mime_type=%s, model=%s",
            session_id,
            audio_size,
            mime_type,
            self.model_name,
        )

        try:
            response = await self.client.post(
                url,
                params=params,
                json=body,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            result = self._parse_voice_response(raw_text)

            logger.info(
                "LLM voice response: session_id=%s, transcription_length=%d, response_length=%d",
                session_id,
                len(result["transcription"]),
                len(result["response"]),
            )
            return result

        except httpx.TimeoutException as e:
            error_msg = mask_token(str(e))
            logger.error("LLM voice timeout: session_id=%s, error=%s", session_id, error_msg)
            raise RuntimeError(f"LLM request timed out: {error_msg}") from e
        except httpx.HTTPStatusError as e:
            error_msg = mask_token(str(e))
            logger.error(
                "LLM voice HTTP error: session_id=%s, status=%d, error=%s",
                session_id,
                e.response.status_code,
                error_msg,
            )
            raise RuntimeError(f"LLM API error: {error_msg}") from e
        except Exception as e:
            error_msg = mask_token(str(e))
            logger.error("LLM voice error: session_id=%s, error=%s", session_id, error_msg)
            raise RuntimeError(f"LLM error: {error_msg}") from e

    @staticmethod
    def _parse_voice_response(raw_text: str) -> dict:
        """
        Parse Gemini response containing [TRANSCRIPTION] and [RESPONSE] markers.
        Falls back to using full text as response if markers not found.
        """
        transcription = ""
        response = ""

        if "[TRANSCRIPTION]" in raw_text and "[RESPONSE]" in raw_text:
            parts = raw_text.split("[RESPONSE]", 1)
            transcription_part = parts[0]
            response = parts[1].strip() if len(parts) > 1 else ""
            transcription = transcription_part.replace("[TRANSCRIPTION]", "").strip()
        else:
            # Fallback: entire text is the response
            response = raw_text.strip()

        return {
            "response": response,
            "transcription": transcription,
        }

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()
