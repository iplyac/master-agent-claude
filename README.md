# AI Agent Service

Stateless AI agent service deployed on Google Cloud Run. Accepts user messages via HTTP,
processes them through a Gemini LLM, and returns text responses. Designed to integrate
seamlessly with the Telegram Bot service.

## Architecture

- **Single process**: uvicorn + FastAPI + httpx LLM client
- **Lifespan management**: LLM client created at startup, closed at shutdown
- **Stateless**: no database, no memory, no sessions — each request is independent
- **Structured logging**: JSON logs with Cloud Trace integration

## Prerequisites

- Docker
- `gcloud` CLI (authenticated: `gcloud auth login`)
- LLM API key (Gemini or compatible endpoint)
- Optional: Google Secret Manager + Application Default Credentials for local secret reads

## API Endpoints

| Method | Path        | Description              |
|--------|-------------|--------------------------|
| GET    | /health     | Health check             |
| GET    | /healthz    | Health check (alias)     |
| POST   | /api/chat   | Process message via LLM  |

### POST /api/chat

Request:
```json
{
  "session_id": "tg_123456",
  "message": "Hello, how are you?"
}
```

Response:
```json
{
  "response": "I'm doing well! How can I help you?"
}
```

## Local Development

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```

2. Set your API key in `.env`:
   ```
   MODEL_API_KEY=your-gemini-api-key
   ```
   Alternatively, configure Application Default Credentials and store the key
   in Secret Manager (secret name: `MODEL_API_KEY`).

3. Build and run locally:
   ```bash
   ./deploy-agent-local.sh
   ```

4. Verify:
   ```bash
   curl http://localhost:8080/health
   # {"status":"ok"}

   curl -X POST http://localhost:8080/api/chat \
     -H 'Content-Type: application/json' \
     -d '{"session_id":"tg_123","message":"hello"}'
   ```

   Without an API key configured, the response will be:
   ```json
   {"response": "AI model not configured. Please contact administrator."}
   ```

## Cloud Run Deployment

Default deployment values:
- SERVICE_NAME=ai-agent
- REGION=europe-west4

### Step 1: Store API key in Secret Manager

```bash
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create MODEL_API_KEY --data-file=-
```

### Step 2: Deploy

```bash
export PROJECT_ID=your-gcp-project
export SERVICE_NAME=ai-agent
export REGION=europe-west4
./deploy-agent.sh
```

For a forced rebuild (no cache):
```bash
./deploy-agent.sh --no-cache
```

### Alternative: Docker Buildx deployment

```bash
export PROJECT_ID=your-gcp-project
./deploy-agent-buildx.sh
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

| Variable                | Required | Default               | Description                     |
|-------------------------|----------|-----------------------|---------------------------------|
| PORT                    | No       | 8080                  | Server port (Cloud Run injects) |
| MODEL_API_KEY           | No       | -                     | LLM API key                     |
| MODEL_API_KEY_SECRET_ID | No       | GOOGLE_API_KEY        | Secret Manager secret name      |
| MODEL_NAME              | No       | gemini-2.0-flash-exp  | LLM model name                  |
| MODEL_ENDPOINT          | No       | Gemini REST API       | Custom LLM endpoint             |
| GCP_PROJECT_ID          | No       | -                     | GCP project ID                  |
| PROJECT_ID              | No       | -                     | GCP project ID (fallback)       |
| REGION                  | No       | europe-west4          | Deployment region               |
| SERVICE_NAME            | No       | ai-agent              | Cloud Run service name          |
| LOG_LEVEL               | No       | INFO                  | Logging level                   |

## Security

- Secrets are excluded from version control via `.gitignore`
- Logs never contain API keys or full message content
- API keys are sanitized (whitespace/control chars removed) and masked in error messages
- Production secrets are managed via Google Secret Manager and mounted as environment variables

## Testing

```bash
pip install -r requirements.txt
pytest tests/
```
