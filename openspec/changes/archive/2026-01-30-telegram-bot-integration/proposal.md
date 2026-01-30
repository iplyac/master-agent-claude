## Why

Telegram-bot сервис должен обращаться к master-agent через Internal Cloud Run DNS. Для этого требуется обновить имя сервиса и настройки ingress в деплой-скрипте. API эндпоинты `/api/chat` и `/api/voice` уже существуют и полностью соответствуют требованиям из INTEGRATION_telegram-bot.md.

## What Changes

- Изменить SERVICE_NAME с `ai-agent` на `master-agent` в `deploy-agent.sh`
- Добавить флаг `--ingress=internal` в команду `gcloud run deploy`
- Опционально: добавить fallback URL через переменную окружения

## Capabilities

### New Capabilities

(нет новых capabilities — API уже реализован)

### Modified Capabilities

- `deployment`: Изменение конфигурации деплоя для работы через Internal DNS

## Impact

- **deploy-agent.sh**: Изменение SERVICE_NAME и добавление ingress флага
- **Cloud Run**: Сервис будет доступен только через VPC (internal traffic)
- **Внешний доступ**: Пропадёт публичный URL — доступ только через Internal DNS или fallback URL
