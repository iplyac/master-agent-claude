# AI Agent Service

AI agent service deployed on Google Cloud Run. Accepts user messages via HTTP,
processes them through Google ADK with Gemini LLM on Vertex AI, and returns text responses.
Designed to integrate seamlessly with the Telegram Bot service.

## Architecture

- **Google ADK**: Agent Development Kit for conversation management
- **Vertex AI**: Gemini models via service account authentication (no API keys)
- **Prompt Management**: System prompts loaded from Vertex AI, reloadable at runtime
- **Session management**: In-memory sessions (not persisted across restarts)
- **Voice support**: Audio transcription via Vertex AI multimodal API
- **Image support**: Image recognition and description via Vertex AI multimodal API
- **Structured logging**: JSON logs with Cloud Trace integration

## Prerequisites

- Docker
- `gcloud` CLI (authenticated: `gcloud auth login`)
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

Response:
```json
{
  "response": "This image shows a cat sitting on a windowsill...",
  "description": "A tabby cat with orange fur sitting on a wooden windowsill."
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

Get the current system prompt.

Response:
```json
{
  "prompt": "You are a helpful AI assistant...",
  "length": 207
}
```

### POST /api/reload-prompt

Reload the system prompt from Vertex AI Prompt Management without restarting the service.

Request: No body required.

Response (success):
```json
{
  "status": "ok",
  "prompt_length": 207
}
```

Response (error - prompt not configured):
```json
{
  "status": "error",
  "error": "AGENT_PROMPT_ID not configured"
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

3. Set environment variables in `.env`:
   ```
   GCP_PROJECT_ID=your-gcp-project
   GCP_LOCATION=europe-west4
   GOOGLE_GENAI_USE_VERTEXAI=true
   ```

4. Run locally:
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 8080
   ```

5. Verify:
   ```bash
   curl http://localhost:8080/health
   # {"status":"ok"}

   curl -X POST http://localhost:8080/api/chat \
     -H 'Content-Type: application/json' \
     -d '{"conversation_id":"test_123","message":"hello"}'
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

**WARNING**: Do not deploy from IDE-embedded terminals (VS Code, IntelliJ, etc.).
They may have restricted environments that cause authentication issues.
Use a standalone terminal application.

If you encounter gcloud permission errors:
```bash
sudo chown -R $(whoami) ~/.config/gcloud
```

## Environment Variables

| Variable                  | Required | Default            | Description                        |
|---------------------------|----------|--------------------|------------------------------------|
| PORT                      | No       | 8080               | Server port (Cloud Run injects)    |
| MODEL_NAME                | No       | gemini-2.0-flash   | LLM model name                     |
| GCP_PROJECT_ID            | No       | -                  | GCP project ID                     |
| GCP_LOCATION              | No       | europe-west4       | Vertex AI location                 |
| GOOGLE_GENAI_USE_VERTEXAI | Yes      | -                  | Must be `true` for Vertex AI       |
| AGENT_PROMPT_ID           | No       | -                  | Vertex AI Prompt ID for dynamic loading |
| REGION                    | No       | europe-west4       | Deployment region                  |
| SERVICE_NAME              | No       | ai-agent           | Cloud Run service name             |
| LOG_LEVEL                 | No       | INFO               | Logging level                      |

## Security

- No API keys required - uses GCP service account authentication
- Logs never contain sensitive message content
- Tokens are masked in error messages

## Documentation

- [Telegram Bot Integration](docs/telegram-bot-integration.md) - Session info endpoint and `/sessioninfo` command

## Testing

```bash
pip install -r requirements.txt
pytest tests/
```
