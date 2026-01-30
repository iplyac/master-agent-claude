# Интеграция с Telegram Bot

Этот документ описывает как telegram-bot будет обращаться к master-agent.

## Обзор

```
┌─────────────────┐                     ┌─────────────────┐
│  telegram-bot   │───Internal DNS────▶ │  master-agent   │
│  (Cloud Run)    │                     │  (Cloud Run)    │
└─────────────────┘                     └─────────────────┘
        │                                       │
        │ VPC Egress                            │ Ingress: internal
        └───────────────── VPC ─────────────────┘
```

## Требования к master-agent

### 1. Имя сервиса (КРИТИЧНО!)

Telegram-bot использует Internal Cloud Run DNS для обнаружения master-agent.
URL формируется как:

```
https://master-agent.{region}.run.internal
```

**Требуется изменить SERVICE_NAME в `deploy-agent.sh`:**

```bash
# Было:
SERVICE_NAME="${SERVICE_NAME:-ai-agent}"

# Должно быть:
SERVICE_NAME="${SERVICE_NAME:-master-agent}"
```

### 2. Ingress настройки

Для работы через Internal DNS, master-agent должен принимать internal traffic.

**Добавить в `gcloud run deploy`:**

```bash
gcloud run deploy "${SERVICE_NAME}" \
    ...
    --ingress=internal \    # ← добавить
    ...
```

Или через консоль: Cloud Run → master-agent → Security → Ingress → "Internal"

### 3. API Endpoints

Telegram-bot использует следующие endpoints:

| Endpoint | Method | Назначение |
|----------|--------|------------|
| `/api/chat` | POST | Текстовые сообщения |
| `/api/voice` | POST | Голосовые сообщения |

#### POST /api/chat

**Request:**
```json
{
  "session_id": "tg_123456789",
  "message": "Привет!"
}
```

**Response (200):**
```json
{
  "response": "Привет! Как я могу помочь?"
}
```

**Response (400):**
```json
{
  "error": "session_id and message are required"
}
```

**Response (500):**
```json
{
  "error": "Agent unavailable, please try again later"
}
```

#### POST /api/voice

**Request:**
```json
{
  "session_id": "tg_123456789",
  "audio_base64": "<base64-encoded-ogg>",
  "mime_type": "audio/ogg"
}
```

**Response (200):**
```json
{
  "response": "Ответ агента на голосовое сообщение",
  "transcription": "Расшифровка голоса"
}
```

### 4. Region

Оба сервиса должны быть в одном регионе для работы Internal DNS.

| Сервис | Текущий регион |
|--------|----------------|
| telegram-bot | `europe-west4` |
| master-agent | `europe-west4` ✓ |

## Изменения в deploy-agent.sh

```diff
--- a/deploy-agent.sh
+++ b/deploy-agent.sh
@@ -4,7 +4,7 @@ set -euo pipefail

 # --- Configuration ---
 PROJECT_ID="${PROJECT_ID:-gen-lang-client-0741140892}"
-SERVICE_NAME="${SERVICE_NAME:-ai-agent}"
+SERVICE_NAME="${SERVICE_NAME:-master-agent}"
 REGION="${REGION:-europe-west4}"
 DOCKER_REGISTRY="${DOCKER_REGISTRY:-gcr.io}"
 LOG_LEVEL="${LOG_LEVEL:-INFO}"
@@ -76,6 +76,7 @@ gcloud run deploy "${SERVICE_NAME}" \
     --region="${REGION}" \
     --image="${IMAGE_LATEST}" \
     --platform=managed \
+    --ingress=internal \
     --allow-unauthenticated \
     --set-env-vars="${ENV_VARS}" \
     --set-secrets="MODEL_API_KEY=GOOGLE_API_KEY:latest" \
```

## Проверка интеграции

После деплоя обоих сервисов:

```bash
# 1. Проверить что master-agent доступен по internal DNS
# (выполнить из контейнера telegram-bot или Cloud Shell в том же VPC)
curl https://master-agent.europe-west4.run.internal/health

# 2. Проверить chat endpoint
curl -X POST https://master-agent.europe-west4.run.internal/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "ping"}'
```

## Fallback

Если VPC не настроен, telegram-bot может использовать env var:

```bash
# В deploy-bot.sh или через Console
AGENT_API_URL=https://master-agent-xxx-ew4.a.run.app
```

Но рекомендуется настроить VPC для Internal DNS.
