## Requirements

### Requirement: Reload prompt endpoint

Сервис SHALL предоставлять эндпоинт для перезагрузки системного промпта из Vertex AI.

#### Scenario: Successful reload
- **WHEN** POST запрос на `/api/reload-prompt`
- **AND** AGENT_PROMPT_ID сконфигурирован
- **THEN** загружается новый промпт из Vertex AI
- **AND** пересоздаётся агент с новым промптом
- **AND** возвращается `{"status": "ok", "prompt_length": <length>}`

#### Scenario: Reload without prompt ID
- **WHEN** POST запрос на `/api/reload-prompt`
- **AND** AGENT_PROMPT_ID не сконфигурирован
- **THEN** возвращается `{"status": "error", "error": "AGENT_PROMPT_ID not configured"}`
- **AND** HTTP status 400

#### Scenario: Reload with Vertex AI error
- **WHEN** POST запрос на `/api/reload-prompt`
- **AND** загрузка промпта из Vertex AI завершается ошибкой
- **THEN** возвращается `{"status": "error", "error": "<message>"}`
- **AND** HTTP status 500
- **AND** текущий агент сохраняется без изменений

### Requirement: Atomic agent replacement

Сервис SHALL заменять агента атомарно при reload.

#### Scenario: Requests during reload
- **WHEN** выполняется reload промпта
- **AND** поступают новые запросы
- **THEN** запросы обрабатываются текущим агентом до завершения reload
- **AND** после reload новые запросы используют обновлённого агента

#### Scenario: Session preservation
- **WHEN** выполняется reload промпта
- **THEN** существующие сессии пользователей сохраняются
- **AND** история сообщений не теряется
