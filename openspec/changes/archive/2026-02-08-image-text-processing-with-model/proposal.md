## Why

Currently, when an image is sent with a text prompt, the system uses Vertex AI (Gemini) to describe the image and then passes the description to the ADK agent. This means the image is only "described" — the user cannot request the model to actually **process or transform** the image (e.g., remove background, apply filters, generate a modified version). By integrating the Nano Banana Pro model for image+text requests, the system can handle image generation/transformation tasks and return a processed image alongside the text response.

## What Changes

- When a request includes **both an image and a text prompt**, route processing to the Nano Banana Pro model instead of the default Gemini pipeline
- The Nano Banana Pro model receives the image + prompt and returns both a text response and a processed/generated image
- The `/api/image` endpoint response is extended to include a `processed_image_base64` field when image transformation is performed
- Requests with **image only** (no prompt) continue using the existing Gemini-based description pipeline
- The model endpoint/configuration for Nano Banana Pro is added as an environment variable

## Capabilities

### New Capabilities
- `image-text-model-processing`: Routing image+text requests to the Nano Banana Pro model, sending the image and prompt, receiving and returning the processed image alongside the text response

### Modified Capabilities
- `image-recognition-api`: The `/api/image` endpoint response now includes an optional `processed_image_base64` field and routes to different models based on whether a text prompt is provided with the image

## Impact

- **API**: `/api/image` response schema extended with optional `processed_image_base64` and `processed_image_mime_type` fields
- **Code**: New model client for Nano Banana Pro integration in `agent/media_client.py` or a new module; routing logic in `agent/processor.py`
- **Dependencies**: May require additional SDK/HTTP client for Nano Banana Pro API
- **Configuration**: New environment variables for Nano Banana Pro endpoint/credentials
- **Backward compatibility**: Requests without a prompt continue to work as before (no breaking changes)
