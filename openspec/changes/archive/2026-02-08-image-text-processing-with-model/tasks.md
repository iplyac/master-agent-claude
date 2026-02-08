## 1. Configuration

- [x] 1.1 Add `get_image_model_name()` function to `agent/config.py` that reads `IMAGE_MODEL_NAME` env var with default `gemini-3-pro-image-preview`

## 2. Model Client

- [x] 2.1 Add `process_image_with_model()` async method to `MediaClient` in `agent/media_client.py` — accepts image_base64, mime_type, session_id, prompt; calls Nano Banana Pro with `response_modalities=['TEXT', 'IMAGE']`; returns dict with `text` and optional `image_base64`/`image_mime_type`
- [x] 2.2 Update `MediaClient.__init__()` to accept and store `image_model_name` parameter

## 3. Response Model

- [x] 3.1 Add optional `processed_image_base64: Optional[str]` and `processed_image_mime_type: Optional[str]` fields to `ImageResponse` in `agent/models.py`

## 4. Processing Logic

- [x] 4.1 Update `MessageProcessor.process_image()` in `agent/processor.py` — when prompt is provided, call `media_client.process_image_with_model()` instead of `describe_image()`; build response dict with `processed_image_base64` and `processed_image_mime_type` fields
- [x] 4.2 Ensure image-only requests (no prompt) still return `processed_image_base64: None` and `processed_image_mime_type: None` for backward compatibility

## 5. App Wiring

- [x] 5.1 Update `app.py` lifespan to pass `get_image_model_name()` to `MediaClient` constructor
- [x] 5.2 Update `/api/image` endpoint to include `processed_image_base64` and `processed_image_mime_type` in the response

## 6. Tests

- [x] 6.1 Add unit tests for `MediaClient.process_image_with_model()` — mock the genai client, test text+image response, text-only response, and error handling
- [x] 6.2 Add unit tests for `MessageProcessor.process_image()` routing — verify prompt triggers model processing, no prompt triggers description
- [x] 6.3 Update existing image endpoint tests to verify new response fields are present (even if null)
