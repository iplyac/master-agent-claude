"""Google Cloud Storage client for persisting images."""

import asyncio
import logging
import time

from google.cloud import storage

logger = logging.getLogger(__name__)

_MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}


def _mime_to_ext(mime_type: str) -> str:
    return _MIME_TO_EXT.get(mime_type, "bin")


class GCSStorageClient:
    """Client for uploading images to Google Cloud Storage."""

    def __init__(self, bucket_name: str):
        self._bucket_name = bucket_name
        self._client = storage.Client()

    def _upload_bytes_sync(self, data: bytes, object_name: str, mime_type: str) -> str:
        """Synchronous upload — called via run_in_executor."""
        bucket = self._client.bucket(self._bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(data, content_type=mime_type)
        return f"gs://{self._bucket_name}/{object_name}"

    async def _upload(self, data: bytes, folder: str, mime_type: str, session_id: str) -> str | None:
        """Upload bytes to GCS. Returns GCS URI or None on error."""
        ext = _mime_to_ext(mime_type)
        timestamp_ms = int(time.time() * 1000)
        object_name = f"{folder}/{session_id}/{timestamp_ms}.{ext}"
        try:
            loop = asyncio.get_event_loop()
            uri = await loop.run_in_executor(
                None, self._upload_bytes_sync, data, object_name, mime_type
            )
            logger.info("GCS upload complete: uri=%s", uri)
            return uri
        except Exception as e:
            logger.warning("GCS upload failed: folder=%s, session_id=%s, error=%s", folder, session_id, e)
            return None

    async def upload_original(self, image_bytes: bytes, mime_type: str, session_id: str) -> str | None:
        """Upload original image to upload/ folder. Returns GCS URI or None on error."""
        return await self._upload(image_bytes, "upload", mime_type, session_id)

    async def upload_processed(self, image_bytes: bytes, mime_type: str, session_id: str) -> str | None:
        """Upload processed image to processed/ folder. Returns GCS URI or None on error."""
        return await self._upload(image_bytes, "processed", mime_type, session_id)

    async def upload_document(self, data: bytes, conversation_id: str, filename: str) -> str:
        """Upload a document to input/ folder. Returns GCS URI. Raises on error.

        Unlike image uploads this is NOT fire-and-forget — a failure prevents
        the docling agent from being called.
        """
        timestamp_ms = int(time.time() * 1000)
        object_name = f"input/{conversation_id}/{timestamp_ms}_{filename}"
        loop = asyncio.get_event_loop()
        uri = await loop.run_in_executor(
            None, self._upload_bytes_sync, data, object_name, "application/octet-stream"
        )
        logger.info("GCS document upload complete: uri=%s", uri)
        return uri
