## Context

The master-agent service currently handles images through the `POST /api/image` endpoint. When an image is sent (with or without a prompt), `MediaClient.describe_image()` uses Vertex AI Gemini to produce a text description, which is then passed to the ADK Runner for a contextual response. The response is always text-only.

Users want the ability to send an image with a text prompt and have the model **process/transform the image** (e.g., edit, modify, generate a new version) using the Nano Banana Pro model (Gemini 3 Pro Image Preview — `gemini-3-pro-image-preview`), returning both a text response and a processed image.

The Nano Banana Pro model is accessible through the same `google.genai` Python SDK already used by `MediaClient`, with `response_modalities=['TEXT', 'IMAGE']` to receive both text and image output.

## Goals / Non-Goals

**Goals:**
- Route image+prompt requests to Nano Banana Pro for image processing/transformation
- Return the processed image (base64) alongside the text response
- Keep image-only requests (no prompt) on the existing Gemini description pipeline
- Reuse the existing `google.genai.Client` infrastructure in `MediaClient`
- Make the Nano Banana Pro model name configurable via environment variable

**Non-Goals:**
- Text-only image generation (no input image) — out of scope
- 4K image generation — use default resolution for now
- Search grounding or thinking mode configuration — use defaults
- Changing voice or chat processing pipelines
- Persisting generated images to storage

## Decisions

### 1. Add `process_image_with_model()` to `MediaClient`

**Decision**: Add a new method to the existing `MediaClient` class rather than creating a separate client.

**Rationale**: `MediaClient` already holds the `google.genai.Client` instance configured for Vertex AI with the correct project/location. Nano Banana Pro uses the same SDK. Adding a method keeps the media processing logic centralized.

**Alternative considered**: A separate `NanoBananaClient` class — rejected because it would duplicate the client setup and add unnecessary abstraction for a single method.

### 2. Routing logic in `MessageProcessor.process_image()`

**Decision**: When `prompt` is provided, call the new `MediaClient.process_image_with_model()` instead of `describe_image()`. When no prompt is provided, keep the existing flow.

**Rationale**: The presence of a prompt is the natural signal that the user wants model-based processing rather than just a description. This is backward-compatible — existing behavior (image without prompt → description) is unchanged.

**Alternative considered**: A separate endpoint (`POST /api/image/process`) — rejected because it fragments the API unnecessarily. The existing endpoint already accepts an optional prompt.

### 3. Model name via environment variable

**Decision**: Add `IMAGE_MODEL_NAME` environment variable (default: `gemini-3-pro-image-preview`). `MediaClient` constructor receives it as a separate parameter.

**Rationale**: Follows the existing pattern of `MODEL_NAME` for the text model. Keeps the image model independently configurable.

### 4. Response format extension

**Decision**: Add optional fields `processed_image_base64` and `processed_image_mime_type` to `ImageResponse`. When Nano Banana Pro is used, these fields are populated. When the existing description flow is used, they are `None`.

**Rationale**: Backward-compatible — existing consumers that only read `response` and `description` are unaffected. The `description` field will contain the text portion of Nano Banana Pro's response when used in the model processing path.

### 5. API call configuration

**Decision**: Use `response_modalities=['TEXT', 'IMAGE']` with the Nano Banana Pro model. Pass the image as `Part.from_bytes()` (already decoded from base64) alongside the text prompt.

**Rationale**: This is the standard SDK pattern for multimodal input/output with Gemini image models. The response parts are iterated to extract both text and inline image data.

## Risks / Trade-offs

- **[Latency increase]** → Nano Banana Pro generation takes 5-15s vs ~1-2s for description-only. Mitigation: This is expected for image processing. Log timing for monitoring.
- **[Cost increase]** → Nano Banana Pro costs ~$0.134/image at 1K-2K resolution. Mitigation: Only used when prompt is provided, not for all image requests.
- **[Model availability]** → `gemini-3-pro-image-preview` is a preview model. Mitigation: Model name is configurable via env var; can switch to GA model when available.
- **[Large response payloads]** → Processed images in base64 can be several MB. Mitigation: Use default resolution (not 4K); consumers should be prepared for larger payloads.
- **[No image returned]** → The model may return only text without an image for some prompts. Mitigation: Handle gracefully — return `None` for image fields and include text response.
