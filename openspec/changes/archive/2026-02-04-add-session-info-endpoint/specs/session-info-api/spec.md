## ADDED Requirements

### Requirement: Session info endpoint

Сервис SHALL предоставлять endpoint `/api/session-info` для получения информации о сессии.

#### Scenario: Get session info for existing session
- **WHEN** POST запрос на `/api/session-info` с `{"conversation_id": "tg_dm_123"}`
- **AND** сессия существует
- **THEN** возвращается JSON с `conversation_id`, `session_id`, `session_exists: true`

#### Scenario: Get session info for non-existing session
- **WHEN** POST запрос на `/api/session-info` с conversation_id
- **AND** сессия не существует
- **THEN** возвращается JSON с `session_exists: false`

#### Scenario: Missing conversation_id
- **WHEN** POST запрос на `/api/session-info` без conversation_id
- **THEN** возвращается HTTP 400 с ошибкой

### Requirement: Response format

Ответ endpoint SHALL содержать стандартизированный JSON формат.

#### Scenario: Success response structure
- **WHEN** запрос успешен
- **THEN** ответ содержит поля: `conversation_id`, `session_id`, `session_exists`

#### Scenario: Optional message count
- **WHEN** session service поддерживает подсчёт сообщений
- **THEN** ответ дополнительно содержит `message_count`
