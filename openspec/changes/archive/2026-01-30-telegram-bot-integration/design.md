## Context

Master-agent — FastAPI сервис на Cloud Run, предоставляющий API для обработки текстовых и голосовых сообщений через Gemini LLM. Telegram-bot должен обращаться к master-agent через Internal Cloud Run DNS (`https://master-agent.europe-west4.run.internal`).

Текущее состояние:
- SERVICE_NAME = `ai-agent` (нужно `master-agent`)
- Ingress = default (нужно `internal`)
- API эндпоинты `/api/chat` и `/api/voice` уже реализованы и соответствуют требованиям

## Goals / Non-Goals

**Goals:**
- Обеспечить доступ telegram-bot к master-agent через Internal DNS
- Сохранить возможность fallback через публичный URL

**Non-Goals:**
- Изменение API эндпоинтов (уже готовы)
- Настройка VPC (делается отдельно)
- Изменение логики обработки сообщений

## Decisions

### 1. Переименование сервиса

**Решение**: Изменить SERVICE_NAME с `ai-agent` на `master-agent`

**Альтернативы**:
- Оставить `ai-agent` и настроить DNS alias → усложняет инфраструктуру
- Использовать переменную окружения для URL → не использует преимущества Internal DNS

**Обоснование**: Internal DNS формирует URL по имени сервиса. Проще изменить имя, чем добавлять alias.

### 2. Internal ingress

**Решение**: Добавить `--ingress=internal` в gcloud run deploy

**Альтернативы**:
- `--ingress=all` с аутентификацией → сложнее настройка, overhead на каждый запрос
- `--ingress=internal-and-cloud-load-balancing` → избыточно для текущих требований

**Обоснование**: Сервис используется только telegram-bot из того же VPC. Internal ingress — самый простой и безопасный вариант.

### 3. Fallback механизм

**Решение**: Документировать возможность использования публичного URL через env var в telegram-bot

**Обоснование**: Если VPC не настроен или нужен доступ извне, telegram-bot может использовать `AGENT_API_URL` env var вместо Internal DNS.

## Risks / Trade-offs

**[Потеря публичного доступа]** → После изменения ingress на internal, сервис не будет доступен извне. **Митигация**: Это ожидаемое поведение. При необходимости внешнего доступа — использовать Cloud Load Balancer.

**[Переименование сервиса]** → Старый сервис `ai-agent` останется в Cloud Run. **Митигация**: Удалить вручную после успешного деплоя `master-agent`.

**[VPC не настроен]** → Internal DNS не будет работать без VPC. **Митигация**: Fallback URL в документации.
