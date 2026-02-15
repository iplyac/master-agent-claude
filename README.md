# Master Agent

AI agent service deployed on Google Cloud Run. Accepts user messages via HTTP,
processes them through Google ADK with Gemini on Vertex AI, and returns text responses.
Designed to integrate with the Telegram Bot service.

## Architecture

- **Google ADK** (`google-adk`): Agent Development Kit — runner, sessions, memory
- **Vertex AI**: Gemini models via service account authentication (no API keys needed)
- **Prompt Management**: System prompts loaded from Vertex AI Prompt Management, reloadable at runtime via `/api/reload-prompt`
- **Sessions**: In-memory by default; persistent Vertex AI Sessions when Agent Engine is configured
- **Memory Bank**: Optional long-term memory via Vertex AI Memory Bank (cross-session context)
- **Voice**: Audio transcription via Gemini multimodal API
- **Image**: Recognition, description, and image generation/editing via Gemini 3 Pro Image Preview
- **Structured logging**: JSON logs with Cloud Trace integration

## Project Structure

```
app.py                  # FastAPI application, lifespan, API endpoints
secret_manager.py       # Google Secret Manager client
agent/
  adk_agent.py          # ADK Agent factory, Vertex AI prompt loader
  config.py             # Environment variable helpers
  media_client.py       # Voice transcription & image processing (genai.Client)
  models.py             # Pydantic request/response models
  processor.py          # MessageProcessor — ADK Runner orchestration
tests/                  # pytest + pytest-asyncio tests
docs/                   # Integration docs
```

## Prerequisites

- Python 3.11+
- `gcloud` CLI (authenticated: `gcloud auth application-default login`)
- GCP project with Vertex AI API enabled
- Service account with `Vertex AI User` role

## API Endpoints

| Method | Path               | Description                    |
|--------|--------------------|--------------------------------|
| GET    | /health            | Health check                   |
| GET    | /healthz           | Health check (alias)           |
| GET    | /api/prompt        | Get current system prompt      |
| POST   | /api/chat          | Process text message           |
| POST   | /api/voice         | Process voice message          |
| POST   | /api/image         | Process image                  |
| POST   | /api/session-info  | Get session information        |
| POST   | /api/reload-prompt | Reload system prompt           |

### POST /api/chat

Request:
```json
{
  "conversation_id": "tg_dm_123456",
  "message": "Hello, how are you?",
  "metadata": {
    "telegram": {
      "chat_id": 123456,
      "user_id": 789,
      "chat_type": "private"
    }
  }
}
```

Response:
```json
{
  "response": "I'm doing well! How can I help you?"
}
```

### POST /api/voice

Request:
```json
{
  "conversation_id": "tg_dm_123456",
  "audio_base64": "<base64-encoded-audio>",
  "mime_type": "audio/ogg",
  "metadata": {
    "telegram": {
      "chat_id": 123456,
      "user_id": 789,
      "chat_type": "private"
    }
  }
}
```

Response:
```json
{
  "response": "Here's my answer to your voice message...",
  "transcription": "What the user said in the audio"
}
```

### POST /api/image

Request:
```json
{
  "conversation_id": "tg_dm_123456",
  "image_base64": "<base64-encoded-image>",
  "mime_type": "image/jpeg",
  "prompt": "What is in this image?",
  "metadata": {
    "telegram": {
      "chat_id": 123456,
      "user_id": 789,
      "chat_type": "private"
    }
  }
}
```

Supported MIME types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`.

Response (without prompt — description only):
```json
{
  "response": "This image shows a cat sitting on a windowsill...",
  "description": "A tabby cat with orange fur sitting on a wooden windowsill."
}
```

Response (with prompt — image processing via Gemini 3 Pro Image Preview):
```json
{
  "response": "Here is your image with the requested changes.",
  "processed_image_base64": "<base64-encoded-result-image>",
  "processed_image_mime_type": "image/png"
}
```

### POST /api/session-info

Request:
```json
{
  "conversation_id": "tg_dm_123456"
}
```

Response:
```json
{
  "conversation_id": "tg_dm_123456",
  "session_id": "tg_dm_123456",
  "session_exists": true,
  "message_count": 5
}
```

### GET /api/prompt

Response:
```json
{
  "prompt": "You are a helpful AI assistant...",
  "length": 207
}
```

### POST /api/reload-prompt

Reload system prompt from Vertex AI Prompt Management without restarting the service. Requires `AGENT_PROMPT_ID` to be configured.

Request: No body required.

Response:
```json
{
  "status": "ok",
  "prompt_length": 207
}
```

## Local Development

1. Authenticate with GCP:
   ```bash
   gcloud auth application-default login
   ```

2. Copy environment template:
   ```bash
   cp .env.example .env
   ```

3. Set your GCP project in `.env`:
   ```
   GCP_PROJECT_ID=your-gcp-project
   GCP_LOCATION=europe-west4
   GOOGLE_GENAI_USE_VERTEXAI=true
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run:
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 8080
   ```

6. Verify:
   ```bash
   curl http://localhost:8080/health
   # {"status":"ok"}

   curl -X POST http://localhost:8080/api/chat \
     -H 'Content-Type: application/json' \
     -d '{"conversation_id":"test_123","message":"hello"}'
   ```

## Testing

```bash
pytest tests/
```

## Cloud Run Deployment

Default deployment values:
- SERVICE_NAME=master-agent
- REGION=europe-west4

### Step 1: Grant Vertex AI access to service account

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Step 2: Deploy

```bash
gcloud run deploy master-agent \
  --source . \
  --region europe-west4 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,GCP_LOCATION=europe-west4,GOOGLE_GENAI_USE_VERTEXAI=true"
```

### Important: Terminal environment

Do not deploy from IDE-embedded terminals (VS Code, IntelliJ, etc.).
They may have restricted environments that cause authentication issues.
Use a standalone terminal application.

## Environment Variables

| Variable                  | Required | Default                  | Description                                         |
|---------------------------|----------|--------------------------|-----------------------------------------------------|
| GCP_PROJECT_ID            | Yes      | -                        | GCP project ID                                      |
| GCP_LOCATION              | No       | europe-west4             | Vertex AI location                                  |
| GOOGLE_GENAI_USE_VERTEXAI | Yes      | -                        | Must be `true` for Vertex AI backend                |
| PORT                      | No       | 8080                     | Server port (Cloud Run injects automatically)       |
| MODEL_NAME                | No       | gemini-2.0-flash         | LLM model name                                      |
| IMAGE_MODEL_NAME          | No       | gemini-3-pro-image-preview | Model for image generation/editing                |
| AGENT_PROMPT_ID           | No       | -                        | Vertex AI Prompt dataset ID for dynamic prompt loading |
| AGENT_ENGINE_ID           | No       | -                        | Agent Engine ID — enables Vertex AI Sessions & Memory Bank |
| REGION                    | No       | europe-west4             | Deployment region                                   |
| SERVICE_NAME              | No       | ai-agent                 | Service name for logging                            |
| LOG_LEVEL                 | No       | INFO                     | Logging level                                       |

## Security

- No API keys — uses GCP service account authentication via Vertex AI
- Logs never contain sensitive message content
- API keys/tokens are masked in error messages

## Documentation

- [Telegram Bot Integration](docs/telegram-bot-integration.md)
