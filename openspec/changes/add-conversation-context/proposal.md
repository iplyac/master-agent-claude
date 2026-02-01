## Why

Сейчас master-agent использует `session_id` для идентификации сессий, но не сохраняет контекст между запросами и не поддерживает маппинг на разные LLM провайдеры. Telegram-bot переходит на новый формат с `conversation_id`, и master-agent должен стать единым центром управления conversation memory.

## What Changes

- Добавить поддержку `conversation_id` в API (с обратной совместимостью для `session_id`)
- Добавить модель `TelegramMetadata` для передачи контекста из Telegram
- Реализовать Conversation Mapping — маппинг `conversation_id` → LLM provider session IDs
- Добавить персистентное хранение маппингов (Firestore)
- Обновить endpoints `/api/chat` и `/api/voice`

## Capabilities

### New Capabilities

- `conversation-mapping`: Маппинг Telegram conversation_id на LLM provider-specific session IDs. Персистентное хранение в Firestore. Поддержка multiple providers.
- `api-v2`: Новый формат API запросов с conversation_id и metadata. Обратная совместимость с session_id (deprecated).

### Modified Capabilities

<!-- Существующие спеки не меняются на уровне требований -->

## Impact

- `app.py` — обновление моделей запросов и endpoints
- Новая зависимость: `google-cloud-firestore`
- Новый модуль: `conversation_store.py` или аналог
- Firestore collection: `conversations`
