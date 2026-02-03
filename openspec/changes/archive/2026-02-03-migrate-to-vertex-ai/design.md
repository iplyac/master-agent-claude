## Context

Сервис master-agent использует Google ADK (v1.2.1) для обработки сообщений через Gemini LLM. Текущая архитектура:

- **LLM Backend**: Google AI API с `GOOGLE_API_KEY` (free tier → rate limits)
- **Session Storage**: Кастомный `FirestoreSessionService` хранит полную историю событий
- **Инициализация**: `Runner` + `Agent` + `FirestoreSessionService` в `app.py`

ADK поддерживает два backend:
1. Google AI API (generativelanguage.googleapis.com) — требует API key
2. Vertex AI (aiplatform.googleapis.com) — использует service account через ADC

## Goals / Non-Goals

**Goals:**
- Переключить LLM backend на Vertex AI для использования project quotas
- Использовать встроенный session service ADK для Vertex AI
- Упростить код, убрав кастомный FirestoreSessionService
- Сохранить текущий API контракт (/api/chat, /api/voice)

**Non-Goals:**
- Изменение логики обработки сообщений
- Миграция существующих сессий из Firestore
- Изменение voice processing (пока остаётся на прямом API)

## Decisions

### Decision 1: Использовать Vertex AI backend через ADK

**Выбор**: Настроить ADK для работы с Vertex AI вместо Google AI API.

**Альтернативы**:
- A) Купить платный API key для Google AI API — не решает проблему архитектуры session storage
- B) Использовать Vertex AI — даёт project quotas + managed session storage

**Реализация**: ADK автоматически выбирает backend на основе переданных параметров. Для Vertex AI нужно:
```python
from google.adk.sessions import VertexAiSessionService

session_service = VertexAiSessionService(
    project=project_id,
    location=region,
)
```

### Decision 2: Удалить кастомный FirestoreSessionService

**Выбор**: Полностью удалить `agent/adk_session_service.py` и использовать `VertexAiSessionService`.

**Альтернативы**:
- A) Оставить Firestore для маппинга telegram_id → session_id — избыточно, ADK сам управляет сессиями по session_id
- B) Полностью перейти на VertexAiSessionService — проще, меньше кода

**Обоснование**: Текущий conversation_id (telegram chat id) можно использовать напрямую как session_id в ADK.

### Decision 3: Аутентификация через service account

**Выбор**: Использовать Application Default Credentials (ADC) вместо API key.

**Реализация**:
- Cloud Run автоматически предоставляет credentials через attached service account
- Нужно добавить роль `Vertex AI User` к service account
- Убрать переменную `GOOGLE_API_KEY` из deployment

### Decision 4: Voice processing (временно на API key)

**Выбор**: Оставить `VoiceClient` на текущей реализации с API key (если нужен), либо отключить.

**Обоснование**: Voice processing использует прямой Gemini API, не ADK. Миграция голоса — отдельная задача.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| VertexAiSessionService может работать иначе | Протестировать локально с эмулятором или в dev environment |
| Потеря существующих сессий в Firestore | Non-goal: старые сессии не мигрируем, начинаем с чистого состояния |
| Service account без нужных прав | Проверить IAM роли перед деплоем: `Vertex AI User` |
| Voice processing сломается без API key | Временно отключить или оставить API key только для voice |

## Migration Plan

1. Добавить IAM роль `Vertex AI User` к Cloud Run service account
2. Обновить код: заменить session service, убрать зависимость от API key
3. Обновить env vars в Cloud Run: GCP_PROJECT_ID, GCP_LOCATION (уже есть europe-west4)
4. Задеплоить и протестировать
5. Удалить секрет GOOGLE_API_KEY (после подтверждения работы)

**Rollback**: Вернуть предыдущую revision Cloud Run через `gcloud run services update-traffic`.
