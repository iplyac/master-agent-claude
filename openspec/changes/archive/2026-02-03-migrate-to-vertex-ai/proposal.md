## Why

Сервис master-agent использует Google AI API (Gemini API) с API ключом из free tier, что приводит к ошибкам 429 RESOURCE_EXHAUSTED после 1-2 запросов. Также используется кастомный FirestoreSessionService для хранения истории сессий, хотя ADK предоставляет встроенное managed хранилище при использовании Vertex AI backend.

Переход на Vertex AI сохраняет доступ к тем же моделям Gemini (gemini-2.0-flash и др.), но с аутентификацией через service account вместо API ключа, что даёт более высокие project-level квоты.

## What Changes

- **BREAKING**: Переключение с Google AI API (generativelanguage.googleapis.com) на Vertex AI (aiplatform.googleapis.com)
- Те же модели Gemini, другой способ аутентификации: service account вместо API ключа
- Замена кастомного `FirestoreSessionService` на встроенный `VertexAiSessionService` из ADK
- Удаление зависимости от `GOOGLE_API_KEY` — Cloud Run автоматически использует attached service account через ADC
- Упрощение кода за счёт использования managed session storage
- Обновление deployment конфигурации: добавить GCP_PROJECT_ID и GCP_LOCATION, убрать GOOGLE_API_KEY

## Capabilities

### New Capabilities

- `vertex-ai-backend`: Конфигурация ADK для работы с Vertex AI вместо Google AI API, включая аутентификацию через service account и настройку project/location

### Modified Capabilities

- `deployment`: Изменение переменных окружения и секретов — убрать GOOGLE_API_KEY, добавить Vertex AI параметры (GCP_PROJECT_ID, GCP_LOCATION)

## Impact

- **Код**: `agent/adk_session_service.py` (удаление), `agent/adk_agent.py` (модификация), `app.py` (модификация инициализации)
- **Конфигурация**: переменные окружения Cloud Run — добавить GCP_PROJECT_ID/GCP_LOCATION, убрать секрет GOOGLE_API_KEY
- **Зависимости**: возможно потребуется дополнительный пакет для Vertex AI session service
- **IAM**: service account Cloud Run должен иметь роль `Vertex AI User` для доступа к LLM и session storage
- **Квоты**: использование project-level квот Vertex AI вместо per-key лимитов Google AI API
