## Why

Переход на Google Agent Development Kit (ADK) для унификации архитектуры агента и использования встроенных механизмов управления сессиями и памятью. ADK предоставляет production-ready инфраструктуру для агентов с поддержкой tools, сессий и персистентной памяти.

## What Changes

- **BREAKING**: Замена ручного LLM-клиента (`llm_client.py`) на ADK Agent
- **BREAKING**: Переход от самописного хранения истории на ADK SessionService с Firestore backend
- Интеграция ADK с существующим FastAPI приложением
- Сохранение текущего API контракта (`/api/chat`, `/api/voice`, `/health`)
- Conversation ID из Telegram продолжит использоваться как session identifier
- Удаление `google-generativeai` в пользу `google-adk`

## Capabilities

### New Capabilities
- `adk-agent`: Конфигурация и инициализация ADK Agent с Gemini моделью
- `adk-session-service`: Интеграция ADK SessionService с Firestore для персистентных сессий

### Modified Capabilities
_(нет изменений в требованиях существующих спек)_

## Impact

**Код:**
- `agent/llm_client.py` — полностью заменяется ADK Agent
- `agent/conversation_store.py` — заменяется на ADK SessionService (возможно частичное сохранение для метаданных)
- `agent/processor.py` — рефакторинг для работы с ADK Runner
- `app.py` — обновление lifespan и эндпоинтов

**Зависимости:**
- Добавить: `google-adk`
- Удалить: `google-generativeai`
- Сохранить: `google-cloud-firestore` (для ADK SessionService backend)

**API:**
- Внешний контракт не меняется — те же endpoints, те же форматы запросов/ответов
- Telegram чат продолжит работать с сохранением контекста между сообщениями
