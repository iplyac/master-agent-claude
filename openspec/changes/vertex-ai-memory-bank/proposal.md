## Why

Сейчас master-agent использует `InMemorySessionService` — вся история разговоров теряется при рестарте сервиса (каждый деплой). Агент не помнит предпочтения пользователя, предыдущие темы и контекст между сессиями. Vertex AI Memory Bank позволяет сохранять долгосрочную память по user_id, чтобы агент мог персонализировать ответы и помнить пользователя через сессии.

## What Changes

- Замена `InMemorySessionService` на `VertexAiSessionService` для сохранения истории сессий в Vertex AI Agent Engine
- Интеграция `VertexAiMemoryBankService` для долгосрочной памяти — автоматическое извлечение фактов из разговоров и хранение по user_id
- Добавление `PreloadMemoryTool` к агенту — автоматическая подгрузка релевантных воспоминаний в начале каждого хода
- Создание Agent Engine instance при первом запуске (или использование существующего по ID из env var)
- Добавление env var `AGENT_ENGINE_ID` для конфигурации
- Сохранение сессий в память после завершения разговора (вызов `add_session_to_memory`)

## Capabilities

### New Capabilities
- `memory-bank`: Интеграция с Vertex AI Memory Bank — долгосрочная память агента, сохранение фактов из разговоров, поиск релевантных воспоминаний при новых обращениях

### Modified Capabilities
- `vertex-ai-backend`: Замена InMemorySessionService на VertexAiSessionService, добавление memory_service в Runner, добавление PreloadMemoryTool к агенту

## Impact

- **Code**: `app.py` (lifespan — новые сервисы), `agent/adk_agent.py` (PreloadMemoryTool), `agent/processor.py` (add_session_to_memory после обработки), `agent/config.py` (новые env vars)
- **Dependencies**: Может потребоваться обновление `google-adk` и `google-cloud-aiplatform` до версий с поддержкой Memory Bank
- **Infrastructure**: Создание Agent Engine instance в GCP проекте
- **Deployment**: Новые env vars: `AGENT_ENGINE_ID`, опционально `MEMORY_BANK_ENABLED`
- **Sessions**: Существующие in-memory сессии будут утеряны (one-time migration, не ломает ничего)
