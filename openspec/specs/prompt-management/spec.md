## Requirements

### Requirement: Load system prompt from Vertex AI

Сервис SHALL загружать системный промпт из Vertex AI Prompt Management при старте.

#### Scenario: Successful prompt load
- **WHEN** сервис запускается
- **AND** env var `AGENT_PROMPT_ID` установлен
- **THEN** загружается промпт из Vertex AI Prompt Management
- **AND** используется как system instruction для агента

#### Scenario: Prompt not configured
- **WHEN** сервис запускается
- **AND** env var `AGENT_PROMPT_ID` не установлен
- **THEN** используется `DEFAULT_INSTRUCTION` из кода

#### Scenario: Prompt load failure
- **WHEN** сервис запускается
- **AND** загрузка промпта из Vertex AI завершается ошибкой
- **THEN** логируется warning
- **AND** используется `DEFAULT_INSTRUCTION` как fallback

### Requirement: Prompt configuration

Конфигурация промпта SHALL осуществляться через environment variables.

#### Scenario: Prompt ID from env
- **WHEN** env var `AGENT_PROMPT_ID` установлен
- **THEN** сервис использует его как resource ID для загрузки промпта

#### Scenario: Project and location from existing config
- **WHEN** загружается промпт
- **THEN** используются `GCP_PROJECT_ID` и `GCP_LOCATION` из существующей конфигурации

### Requirement: Dynamic prompt update

Сервис SHALL поддерживать динамическое обновление системного промпта в runtime.

#### Scenario: Prompt update in memory
- **WHEN** загружен новый промпт
- **THEN** создаётся новый Agent с новым промптом
- **AND** создаётся новый Runner с новым агентом
- **AND** обновляется `app.state.runner`

#### Scenario: Mutable agent storage
- **WHEN** сервис запускается
- **THEN** agent и runner хранятся в `app.state`
- **AND** могут быть заменены при reload
