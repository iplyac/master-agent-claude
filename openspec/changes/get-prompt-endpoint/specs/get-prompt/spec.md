## ADDED Requirements

### Requirement: Get prompt endpoint

Сервис SHALL предоставлять эндпоинт для получения текущего системного промпта.

#### Scenario: Get current prompt
- **WHEN** GET запрос на `/api/prompt`
- **THEN** возвращается `{"prompt": "<text>", "length": <int>}`
- **AND** HTTP status 200

#### Scenario: Prompt not configured
- **WHEN** GET запрос на `/api/prompt`
- **AND** агент использует DEFAULT_INSTRUCTION
- **THEN** возвращается текст DEFAULT_INSTRUCTION
- **AND** HTTP status 200
