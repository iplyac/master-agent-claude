## Context

Master-agent обрабатывает сообщения от telegram-bot, используя conversation_id для идентификации сессии. Сейчас нет способа проверить, какой session_id соответствует конкретному Telegram чату.

Текущая архитектура:
- telegram-bot отправляет запросы с `conversation_id` = `tg_dm_{chat_id}` или `tg_group_{chat_id}`
- master-agent использует `conversation_id` как `session_id` в ADK

## Goals / Non-Goals

**Goals:**
- Добавить endpoint для получения информации о сессии по conversation_id
- Возвращать: conversation_id, session_id, статус сессии
- Подготовить инструкцию для интеграции в telegram-bot

**Non-Goals:**
- Изменение логики работы сессий
- Административные операции над сессиями (удаление, очистка)
- Аутентификация/авторизация для endpoint

## Decisions

### Decision 1: POST endpoint `/api/session-info`

**Выбор**: POST вместо GET, чтобы передавать conversation_id в body.

**Формат запроса:**
```json
{
  "conversation_id": "tg_dm_234759359"
}
```

**Формат ответа:**
```json
{
  "conversation_id": "tg_dm_234759359",
  "session_id": "tg_dm_234759359",
  "session_exists": true,
  "message_count": 5
}
```

### Decision 2: Инструкция как markdown файл

**Выбор**: Создать `docs/telegram-bot-integration.md` с инструкцией для Claude Code агента.

**Содержание:**
- Описание endpoint
- Пример вызова
- Код для добавления команды `/sessioninfo` в telegram-bot

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Endpoint доступен без аутентификации | Возвращает только метаданные, не содержимое сессии |
| InMemorySessionService не хранит message_count | Вернуть null или опустить поле |
