## ADDED Requirements

### Requirement: New request format with conversation_id

API SHALL принимать новый формат запроса с `conversation_id` и `metadata`.

#### Scenario: New format accepted
- **WHEN** запрос содержит `conversation_id` и `message`
- **THEN** запрос обрабатывается успешно

### Requirement: TelegramMetadata in requests

API SHALL принимать опциональный `metadata.telegram` объект с информацией о чате.

#### Scenario: Metadata provided
- **WHEN** запрос содержит `metadata.telegram` с `chat_id`, `user_id`, `chat_type`
- **THEN** metadata логируется и может использоваться для бизнес-логики

#### Scenario: Metadata omitted
- **WHEN** запрос не содержит `metadata`
- **THEN** запрос обрабатывается без metadata

### Requirement: Backward compatibility with session_id

API SHALL поддерживать старый формат с `session_id` для обратной совместимости.

#### Scenario: Old format accepted
- **WHEN** запрос содержит `session_id` вместо `conversation_id`
- **THEN** запрос обрабатывается, `session_id` используется как `conversation_id`

#### Scenario: Deprecation warning logged
- **WHEN** используется старый формат с `session_id`
- **THEN** в логах появляется deprecation warning

### Requirement: conversation_id priority over session_id

Если указаны оба поля, `conversation_id` SHALL иметь приоритет.

#### Scenario: Both fields provided
- **WHEN** запрос содержит и `conversation_id`, и `session_id`
- **THEN** используется `conversation_id`, `session_id` игнорируется

### Requirement: Validation error on missing identifiers

API SHALL возвращать ошибку если не указан ни `conversation_id`, ни `session_id`.

#### Scenario: No identifier provided
- **WHEN** запрос не содержит ни `conversation_id`, ни `session_id`
- **THEN** возвращается 400 Bad Request с сообщением об ошибке

### Requirement: Voice endpoint support

Endpoint `/api/voice` SHALL поддерживать тот же формат что и `/api/chat`.

#### Scenario: Voice with new format
- **WHEN** `/api/voice` получает запрос с `conversation_id`
- **THEN** запрос обрабатывается с использованием conversation mapping

### Requirement: conversation_id format

conversation_id SHALL следовать формату определённому Telegram-bot.

#### Scenario: Private chat format
- **WHEN** chat_type = "private"
- **THEN** conversation_id имеет формат `tg_dm_{user_id}`

#### Scenario: Group chat format
- **WHEN** chat_type = "group" или "supergroup"
- **THEN** conversation_id имеет формат `tg_group_{chat_id}`
