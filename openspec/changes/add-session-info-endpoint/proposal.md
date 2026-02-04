## Why

Для отладки и мониторинга интеграции между telegram-bot и master-agent нужен способ узнать текущий ID чата в Telegram и соответствующий session ID в master-agent. Это позволит проверять корректность маппинга и отлаживать проблемы с контекстом сессий.

## What Changes

- Добавить новый endpoint `/api/session-info` в master-agent, который возвращает информацию о сессии по conversation_id
- Подготовить инструкцию для Claude Code агента по добавлению команды `/sessioninfo` в telegram-bot

## Capabilities

### New Capabilities

- `session-info-api`: Endpoint для получения информации о сессии (conversation_id → session details)

### Modified Capabilities

_Нет изменений в существующих capabilities_

## Impact

- **Код**: `app.py` — новый endpoint `/api/session-info`
- **API**: Новый GET/POST endpoint, не влияет на существующие
- **Документация**: Инструкция для интеграции в telegram-bot
- **Внешние системы**: telegram-bot потребует изменений для вызова нового endpoint
